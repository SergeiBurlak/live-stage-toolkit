// ShowNetSubsystem.h
// Deterministic Art-Net / sACN output for UE5 with an isolated sender thread,
// watchdog blackout and E-STOP latch. Decouples DMX output rate from the render
// thread so GPU hitches never translate into dropped lighting/laser frames.
//
// Module dependencies (Build.cs): "Core", "CoreUObject", "Engine", "Sockets", "Networking"
//
// IMPORTANT - two behaviours that are easy to get wrong when wiring this in:
//
// 1. KeepAlive() must come from an actual per-frame source (Event Tick, or a
//    dedicated fast repeating timer) - NOT from a Delay-node chain. This
//    project's only proven Blueprint trigger pattern (BP_ConfettiConductor)
//    is built on sequential Delay nodes, which can be seconds apart. If
//    KeepAlive() is wired the same way, the watchdog will see gaps far
//    longer than its timeout between calls and will force every universe to
//    blackout between each Delay firing - lights will flicker to black
//    continuously even though nothing has actually frozen. Call KeepAlive()
//    every Tick (or from a Set Timer by Function Name at >= 10-20 Hz),
//    independently of whatever chain is driving the show content itself.
//
// 2. Configure() silently clears any latched EmergencyStop(). If the show
//    controller calls Configure() again after an emergency stop (e.g. to
//    change the target IP, or defensively on BeginPlay), the stop is
//    released without an explicit ClearEmergencyStop() call. This is
//    intentional (a full reconfigure is treated as a fresh start), but it
//    means EmergencyStop() is NOT a substitute for physically confirming the
//    rig is safe before Configure() is called again mid-show. A warning is
//    logged (LogShowNet) whenever Configure() clears an active stop, so this
//    is at least visible in the Output Log rather than silent.

#pragma once

#include "CoreMinimal.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "HAL/ThreadSafeBool.h"
#include "Misc/ScopeLock.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "ShowNetSubsystem.generated.h"

class FSocket;
class FInternetAddr;

/** One DMX512 universe worth of channel data. */
USTRUCT(BlueprintType)
struct FShowNetUniverse
{
	GENERATED_BODY()

	/** Art-Net 15-bit port address: Net<<8 | SubUni. 0..32767 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ShowNet")
	int32 PortAddress = 0;

	/** 512 channel values. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ShowNet")
	TArray<uint8> Channels;

	FShowNetUniverse()
	{
		Channels.Init(0, 512);
	}
};

/** Runtime statistics, polled from Blueprints / on-stage HUD. */
USTRUCT(BlueprintType)
struct FShowNetStats
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "ShowNet")
	int64 PacketsSent = 0;

	UPROPERTY(BlueprintReadOnly, Category = "ShowNet")
	int64 SendErrors = 0;

	/** Worst observed sender-loop interval in milliseconds since last reset. */
	UPROPERTY(BlueprintReadOnly, Category = "ShowNet")
	float WorstLoopIntervalMs = 0.f;

	/** Milliseconds since the game thread last fed the watchdog. */
	UPROPERTY(BlueprintReadOnly, Category = "ShowNet")
	float TimeSinceKeepAliveMs = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "ShowNet")
	bool bBlackoutActive = false;

	UPROPERTY(BlueprintReadOnly, Category = "ShowNet")
	bool bEmergencyStopLatched = false;
};

/**
 * Show network output subsystem.
 *
 * Usage:
 *   ShowNet->Configure(TEXT("2.0.0.255"), 6454, 44.f, 250.f);
 *   ShowNet->RegisterUniverse(0);
 *   ShowNet->SetChannel(0, 1, 255);   // universe port address 0, channel 1 (1-based)
 *   ShowNet->KeepAlive();             // call every frame from the show controller
 *
 * See the file header above for two behaviours that are easy to wire wrong:
 * KeepAlive() must be a per-frame call (not a Delay-chain step), and
 * Configure() silently clears EmergencyStop().
 */
UCLASS()
class UShowNetSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/**
	 * @param InTargetIp        Unicast or directed-broadcast address of the Art-Net node (e.g. "2.0.0.255").
	 * @param InPort            Art-Net UDP port (standard 6454).
	 * @param InRefreshHz       Output rate. DMX512 physical maximum is ~44 Hz per universe.
	 * @param InWatchdogMs      If the game thread stops calling KeepAlive() for this long, output goes to blackout.
	 *                          Floored at 100 ms: a typical 30 fps game thread ticks every ~33 ms, so a lower
	 *                          value risks tripping the watchdog on ordinary frame-time variance rather than
	 *                          on a genuine freeze. If you need a tighter margin, first confirm KeepAlive() is
	 *                          driven by Tick (see the file header), not a Delay chain.
	 *
	 * NOTE: calling Configure() again on an already-configured subsystem replaces the sender and silently
	 * clears any latched EmergencyStop() - see the file header. A warning is logged if this happens while a
	 * stop was active.
	 */
	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	bool Configure(const FString& InTargetIp, int32 InPort = 6454, float InRefreshHz = 44.f, float InWatchdogMs = 250.f);

	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	void RegisterUniverse(int32 PortAddress);

	/** Channel is 1-based (DMX convention). Thread-safe. */
	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	void SetChannel(int32 PortAddress, int32 Channel, uint8 Value);

	/** Bulk write; Values may be shorter than 512. Thread-safe. */
	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	void SetChannels(int32 PortAddress, int32 StartChannel, const TArray<uint8>& Values);

	/**
	 * Feed the watchdog. Must be called every frame - from Event Tick or an
	 * equivalent fast repeating timer, NEVER from a Delay-node chain (see the
	 * file header for why: this project's proven Delay-chain trigger pattern
	 * fires far too infrequently for a watchdog and will cause constant
	 * false blackouts if used here).
	 */
	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	void KeepAlive();

	/** Latches a hard blackout on every universe until ClearEmergencyStop() is called. */
	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	void EmergencyStop();

	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	void ClearEmergencyStop();

	UFUNCTION(BlueprintCallable, Category = "ShowNet")
	FShowNetStats GetStats() const;

private:
	friend class FShowNetSender;

	/** Tears down any existing Sender/SenderThread pair, regardless of which one is non-null. */
	void ShutdownSender();

	/** Sender thread implementation. */
	class FShowNetSender* Sender = nullptr;
	FRunnableThread* SenderThread = nullptr;
};

/** Isolated, fixed-rate Art-Net sender. Never touches UObjects. */
class FShowNetSender : public FRunnable
{
public:
	FShowNetSender(const FString& InTargetIp, int32 InPort, float InRefreshHz, float InWatchdogMs);
	virtual ~FShowNetSender();

	virtual bool Init() override;
	virtual uint32 Run() override;
	virtual void Stop() override;
	virtual void Exit() override;

	void RegisterUniverse(int32 PortAddress);
	void SetChannel(int32 PortAddress, int32 Channel, uint8 Value);
	void SetChannels(int32 PortAddress, int32 StartChannel, const TArray<uint8>& Values);
	void KeepAlive();
	void SetEmergencyStop(bool bEnabled);
	bool IsEmergencyStopped() const;
	FShowNetStats Snapshot() const;
	bool IsSocketValid() const { return Socket != nullptr; }

private:
	void BuildArtDmxPacket(int32 PortAddress, const uint8* Data, uint8 Sequence, TArray<uint8>& OutPacket) const;

	FSocket* Socket = nullptr;
	TSharedPtr<FInternetAddr> RemoteAddr;

	FString TargetIp;
	int32 Port = 6454;
	double PeriodSeconds = 1.0 / 44.0;
	double WatchdogSeconds = 0.25;

	mutable FCriticalSection DataGuard;
	TMap<int32, TArray<uint8>> Universes;      // PortAddress -> 512 bytes
	TMap<int32, uint8> SequenceCounters;       // PortAddress -> Art-Net sequence

	FThreadSafeBool bStopRequested = false;
	FThreadSafeBool bEmergencyStop = false;

	mutable FCriticalSection StatsGuard;
	FShowNetStats Stats;
	double LastKeepAliveTime = 0.0;
};
