// ShowNetSubsystem.h
// Deterministic Art-Net / sACN output for UE5 with an isolated sender thread,
// watchdog blackout and E-STOP latch. Decouples DMX output rate from the render
// thread so GPU hitches never translate into dropped lighting/laser frames.
//
// Module dependencies (Build.cs): "Core", "CoreUObject", "Engine", "Sockets", "Networking"

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

	/** Feed the watchdog. Call once per game-thread tick from the show controller actor. */
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
