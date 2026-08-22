// ShowNetSubsystem.cpp

#include "ShowNetSubsystem.h"

#include "Common/UdpSocketBuilder.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "IPAddress.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformTime.h"

DEFINE_LOG_CATEGORY_STATIC(LogShowNet, Log, All);

// ---------------------------------------------------------------------------
// FShowNetSender
// ---------------------------------------------------------------------------

FShowNetSender::FShowNetSender(const FString& InTargetIp, int32 InPort, float InRefreshHz, float InWatchdogMs)
	: TargetIp(InTargetIp)
	, Port(InPort)
	, PeriodSeconds(1.0 / FMath::Clamp(InRefreshHz, 1.f, 44.f))
	, WatchdogSeconds(FMath::Max(InWatchdogMs, 20.f) / 1000.0)
{
	LastKeepAliveTime = FPlatformTime::Seconds();
}

FShowNetSender::~FShowNetSender()
{
	if (Socket)
	{
		ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
		Socket->Close();
		if (SocketSubsystem)
		{
			SocketSubsystem->DestroySocket(Socket);
		}
		Socket = nullptr;
	}
}

bool FShowNetSender::Init()
{
	ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!SocketSubsystem)
	{
		UE_LOG(LogShowNet, Error, TEXT("No socket subsystem available."));
		return false;
	}

	bool bIsValidIp = false;
	RemoteAddr = SocketSubsystem->CreateInternetAddr();
	RemoteAddr->SetIp(*TargetIp, bIsValidIp);
	RemoteAddr->SetPort(Port);

	if (!bIsValidIp)
	{
		UE_LOG(LogShowNet, Error, TEXT("Invalid Art-Net target address: %s"), *TargetIp);
		return false;
	}

	Socket = FUdpSocketBuilder(TEXT("ShowNetArtNet"))
				 .AsReusable()
				 .WithBroadcast()
				 .WithSendBufferSize(64 * 1024)
				 .Build();

	if (!Socket)
	{
		UE_LOG(LogShowNet, Error, TEXT("Failed to create Art-Net UDP socket."));
		return false;
	}

	UE_LOG(LogShowNet, Log, TEXT("Art-Net sender ready: %s:%d at %.1f Hz"), *TargetIp, Port, 1.0 / PeriodSeconds);
	return true;
}

void FShowNetSender::BuildArtDmxPacket(int32 PortAddress, const uint8* Data, uint8 Sequence, TArray<uint8>& OutPacket) const
{
	// ArtDmx: 18-byte header + 512 data bytes.
	OutPacket.SetNumUninitialized(18 + 512, EAllowShrinking::No);

	const char Id[8] = { 'A', 'r', 't', '-', 'N', 'e', 't', '\0' };
	FMemory::Memcpy(OutPacket.GetData(), Id, 8);

	OutPacket[8]  = 0x00;                                   // OpCode lo (OpOutput/OpDmx = 0x5000, little endian)
	OutPacket[9]  = 0x50;                                   // OpCode hi
	OutPacket[10] = 0x00;                                   // ProtVerHi
	OutPacket[11] = 14;                                     // ProtVerLo
	OutPacket[12] = Sequence;                               // 0 = disable sequencing, else 1..255
	OutPacket[13] = 0x00;                                   // Physical (informational)
	OutPacket[14] = static_cast<uint8>(PortAddress & 0xFF); // SubUni
	OutPacket[15] = static_cast<uint8>((PortAddress >> 8) & 0x7F); // Net
	OutPacket[16] = 0x02;                                   // LengthHi (512)
	OutPacket[17] = 0x00;                                   // LengthLo

	FMemory::Memcpy(OutPacket.GetData() + 18, Data, 512);
}

uint32 FShowNetSender::Run()
{
	TArray<uint8> Packet;
	Packet.Reserve(530);

	TArray<uint8> Blackout;
	Blackout.Init(0, 512);

	double NextSendTime = FPlatformTime::Seconds();
	double LastLoopTime = NextSendTime;

	while (!bStopRequested)
	{
		const double Now = FPlatformTime::Seconds();

		if (Now < NextSendTime)
		{
			// Sleep in small slices to keep jitter below one DMX frame.
			const double Remaining = NextSendTime - Now;
			FPlatformProcess::SleepNoStats(static_cast<float>(FMath::Min(Remaining, 0.001)));
			continue;
		}

		// Fixed-rate scheduling with catch-up clamp: never burst more than one frame.
		NextSendTime += PeriodSeconds;
		if (NextSendTime < Now)
		{
			NextSendTime = Now + PeriodSeconds;
		}

		const double LoopIntervalMs = (Now - LastLoopTime) * 1000.0;
		LastLoopTime = Now;

		double SinceKeepAlive = 0.0;
		{
			FScopeLock Lock(&StatsGuard);
			SinceKeepAlive = Now - LastKeepAliveTime;
		}

		const bool bWatchdogTripped = SinceKeepAlive > WatchdogSeconds;
		const bool bForceZero = bWatchdogTripped || bEmergencyStop;

		TArray<int32> Addresses;
		{
			FScopeLock Lock(&DataGuard);
			Universes.GetKeys(Addresses);

			for (int32 Address : Addresses)
			{
				const TArray<uint8>* Source = bForceZero ? &Blackout : Universes.Find(Address);
				uint8& Seq = SequenceCounters.FindOrAdd(Address);
				Seq = (Seq == 255) ? 1 : Seq + 1;

				BuildArtDmxPacket(Address, Source->GetData(), Seq, Packet);

				int32 BytesSent = 0;
				const bool bOk = Socket->SendTo(Packet.GetData(), Packet.Num(), BytesSent, *RemoteAddr);

				FScopeLock StatLock(&StatsGuard);
				if (bOk && BytesSent == Packet.Num())
				{
					++Stats.PacketsSent;
				}
				else
				{
					++Stats.SendErrors;
				}
			}
		}

		FScopeLock StatLock(&StatsGuard);
		Stats.WorstLoopIntervalMs = FMath::Max(Stats.WorstLoopIntervalMs, static_cast<float>(LoopIntervalMs));
		Stats.TimeSinceKeepAliveMs = static_cast<float>(SinceKeepAlive * 1000.0);
		Stats.bBlackoutActive = bForceZero;
		Stats.bEmergencyStopLatched = bEmergencyStop;
	}

	// Graceful shutdown: three blackout frames so fixtures cannot latch on a stale value.
	{
		FScopeLock Lock(&DataGuard);
		TArray<int32> Addresses;
		Universes.GetKeys(Addresses);
		for (int32 Pass = 0; Pass < 3; ++Pass)
		{
			for (int32 Address : Addresses)
			{
				uint8& Seq = SequenceCounters.FindOrAdd(Address);
				Seq = (Seq == 255) ? 1 : Seq + 1;
				BuildArtDmxPacket(Address, Blackout.GetData(), Seq, Packet);
				int32 BytesSent = 0;
				Socket->SendTo(Packet.GetData(), Packet.Num(), BytesSent, *RemoteAddr);
			}
			FPlatformProcess::Sleep(0.023f);
		}
	}

	return 0;
}

void FShowNetSender::Stop()
{
	bStopRequested = true;
}

void FShowNetSender::Exit()
{
}

void FShowNetSender::RegisterUniverse(int32 PortAddress)
{
	FScopeLock Lock(&DataGuard);
	if (!Universes.Contains(PortAddress))
	{
		TArray<uint8> Fresh;
		Fresh.Init(0, 512);
		Universes.Add(PortAddress, MoveTemp(Fresh));
		SequenceCounters.Add(PortAddress, 0);
	}
}

void FShowNetSender::SetChannel(int32 PortAddress, int32 Channel, uint8 Value)
{
	if (Channel < 1 || Channel > 512)
	{
		return;
	}

	FScopeLock Lock(&DataGuard);
	if (TArray<uint8>* Data = Universes.Find(PortAddress))
	{
		(*Data)[Channel - 1] = Value;
	}
}

void FShowNetSender::SetChannels(int32 PortAddress, int32 StartChannel, const TArray<uint8>& Values)
{
	if (StartChannel < 1 || StartChannel > 512)
	{
		return;
	}

	FScopeLock Lock(&DataGuard);
	if (TArray<uint8>* Data = Universes.Find(PortAddress))
	{
		const int32 Count = FMath::Min(Values.Num(), 512 - (StartChannel - 1));
		FMemory::Memcpy(Data->GetData() + (StartChannel - 1), Values.GetData(), Count);
	}
}

void FShowNetSender::KeepAlive()
{
	FScopeLock Lock(&StatsGuard);
	LastKeepAliveTime = FPlatformTime::Seconds();
}

void FShowNetSender::SetEmergencyStop(bool bEnabled)
{
	bEmergencyStop = bEnabled;
}

FShowNetStats FShowNetSender::Snapshot() const
{
	FScopeLock Lock(&StatsGuard);
	return Stats;
}

// ---------------------------------------------------------------------------
// UShowNetSubsystem
// ---------------------------------------------------------------------------

void UShowNetSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
}

void UShowNetSubsystem::Deinitialize()
{
	if (SenderThread)
	{
		Sender->Stop();
		SenderThread->WaitForCompletion();
		delete SenderThread;
		SenderThread = nullptr;
	}

	if (Sender)
	{
		delete Sender;
		Sender = nullptr;
	}

	Super::Deinitialize();
}

bool UShowNetSubsystem::Configure(const FString& InTargetIp, int32 InPort, float InRefreshHz, float InWatchdogMs)
{
	if (SenderThread)
	{
		Sender->Stop();
		SenderThread->WaitForCompletion();
		delete SenderThread;
		SenderThread = nullptr;
		delete Sender;
		Sender = nullptr;
	}

	Sender = new FShowNetSender(InTargetIp, InPort, InRefreshHz, InWatchdogMs);
	if (!Sender->Init())
	{
		delete Sender;
		Sender = nullptr;
		return false;
	}

	SenderThread = FRunnableThread::Create(Sender, TEXT("ShowNetSender"), 0, TPri_AboveNormal);
	return SenderThread != nullptr;
}

void UShowNetSubsystem::RegisterUniverse(int32 PortAddress)
{
	if (Sender)
	{
		Sender->RegisterUniverse(PortAddress);
	}
}

void UShowNetSubsystem::SetChannel(int32 PortAddress, int32 Channel, uint8 Value)
{
	if (Sender)
	{
		Sender->SetChannel(PortAddress, Channel, Value);
	}
}

void UShowNetSubsystem::SetChannels(int32 PortAddress, int32 StartChannel, const TArray<uint8>& Values)
{
	if (Sender)
	{
		Sender->SetChannels(PortAddress, StartChannel, Values);
	}
}

void UShowNetSubsystem::KeepAlive()
{
	if (Sender)
	{
		Sender->KeepAlive();
	}
}

void UShowNetSubsystem::EmergencyStop()
{
	if (Sender)
	{
		Sender->SetEmergencyStop(true);
	}
}

void UShowNetSubsystem::ClearEmergencyStop()
{
	if (Sender)
	{
		Sender->SetEmergencyStop(false);
	}
}

FShowNetStats UShowNetSubsystem::GetStats() const
{
	return Sender ? Sender->Snapshot() : FShowNetStats();
}
