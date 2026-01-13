//
//  SpheroRunner.swift
//  IOTTools
//
//  Created by Emmanuel Moulin on 02/12/2025.
//

import Foundation
import Pappe

/// Runner dedicated to Sphero-like devices (Mini / Bolt).
/// - Uses Synchrosphere + Pappe the same way as RoverRunner.
/// - Executes pending commands synchronously in the Pappe loop.
/// - Reads command duration (ms) for forward/back/turn (default handled by RobotCommand).
final class SpheroRunner {

    // MARK: - Properties

    unowned let robot: Robot

    private let engine = SyncsEngine()
    private var controller: SyncsController?
    private var config: SyncsControllerConfig?

    /// Next command to execute (nil = idle)
    var pendingCommand: RobotCommand?

    // MARK: - Init

    init(robot: Robot) {
        self.robot = robot
    }

    // MARK: - Connect

    func connect() {

        //------------------------------------------------------
        // 1) Configure controller (logs + callbacks)
        //------------------------------------------------------
        // Use specific device name if provided, otherwise connect to any Bolt
        let deviceSelector: SyncsDeviceSelector = robot.bluetoothName.isEmpty
            ? .anyBolt
            : .specificBolt(name: robot.bluetoothName)

        var cfg = SyncsControllerConfig(deviceSelector: deviceSelector)
        cfg.logLevel = .info

        cfg.stateDidChangeCallback = { [weak self] state in
            guard let self = self else { return }

            // Consider "connected" once the robot is awake.
            if state.contains(.isAwake), !self.robot.isConnected {
                DispatchQueue.main.async { self.robot._didConnect() }
            }

            // Consider "disconnected" if the BLE link drops.
            if !state.contains(.isConnected), self.robot.isConnected {
                DispatchQueue.main.async { self.robot._didDisconnect() }
            }

            // Best-effort battery feedback from controller state flags.
            if state.contains(.isBatteryCritical) {
                DispatchQueue.main.async { self.robot._updateBattery(from: .critical) }
            } else if state.contains(.isBatteryLow) {
                DispatchQueue.main.async { self.robot._updateBattery(from: .low) }
            } else {
                DispatchQueue.main.async { self.robot._updateBattery(from: .ok) }
            }
        }

        self.config = cfg

        //------------------------------------------------------
        // 2) Build Pappe controller
        //------------------------------------------------------
        controller = engine.makeController(for: cfg) { names, ctx in

            activity(names.Main, [
                "cmdSpeed",
                "cmdHeading",
                "cmdDir",
                "cmdSeconds",
                "cmdColor",
                "doRollForSeconds",
                "doStop",
                "doSetLED",
                "doVibrate",
                "doSpin",
                "sample",
                "counter"
            ]) { val in

                //------------------------------------------------------
                // Initialize Pappe vars once
                //------------------------------------------------------
                exec {
                    val.cmdSpeed = SyncsSpeed(0)
                    val.cmdHeading = SyncsHeading(0)
                    val.cmdDir = SyncsDir.forward
                    val.cmdSeconds = 1
                    
                    val.cmdColor = SyncsColor(red: 0, green: 0, blue: 0)

                    val.doRollForSeconds = false
                    val.doStop = false
                    val.doSetLED = false
                    val.doVibrate = false
                    val.doSpin = false
                    val.sample = SyncsSample.unset
                }
                
                cobegin {
                    with {
                        // Stream sensors at 10Hz
                        run(Syncs.SensorStreamer, [
                            10,
                            SyncsSensors([.acceleration, .location, .velocity, .yaw])
                        ], [val.loc.sample])
                    }
                    
                    with {
                        //------------------------------------------------------
                        // Main control loop
                        //------------------------------------------------------
                        `repeat` {
                            
                            //------------------------------------------------------
                            // 1) SWIFT → PAPPE binding (allowed here)
                            //------------------------------------------------------
                            exec {
                                let rawSample: Any? = val.sample
                                if let s = rawSample as? SyncsSample, s.timestamp > 0 {
                                    self.robot._updateFrom(syncsSample: s)
                                }
                                
                                // Reset flags
                                val.doRollForSeconds = false
                                val.doStop = false
                                val.doSetLED = false
                                val.doVibrate = false
                                val.doSpin = false
                                
                                guard let cmd = self.pendingCommand else { return }
                                
                                // Helpers (Swift only)
                                func clampSpeed(_ s: Int) -> SyncsSpeed {
                                    let v = max(0, min(255, s))
                                    return SyncsSpeed(UInt8(v))
                                }
                                
                                func clampHeading(_ h: Int) -> SyncsHeading {
                                    // normalize to 0...359
                                    let norm = ((h % 360) + 360) % 360
                                    return SyncsHeading(UInt16(norm))
                                }
                                
                                func msToSeconds(_ ms: Int) -> Int {
                                    // Synchrosphere offers RollForSeconds(seconds: Int)
                                    // Keep it simple: minimum 1 second.
                                    let clamped = max(1, ms)
                                    let secs = Int(ceil(Double(clamped) / 1000.0))
                                    return max(1, secs)
                                }
                                
                                // Defaults
                                var speed: SyncsSpeed = 0
                                var heading: SyncsHeading = clampHeading(self.robot.heading)
                                var dir: SyncsDir = .forward
                                var seconds: Int = 1
                                var color = SyncsColor(red: 0, green: 0, blue: 0)
                                
                                var shouldRoll = false
                                var shouldStop = false
                                var shouldSetLED = false
                                var shouldVibrate = false
                                var shouldSpin = false
                                
                                switch cmd {
                                    
                                case .forward(let s, let durationMs):
                                    speed = clampSpeed(s)
                                    heading = clampHeading(self.robot.heading)
                                    dir = SyncsDir.forward
                                    seconds = msToSeconds(durationMs)
                                    shouldRoll = true
                                    
                                case .backward(let s, let durationMs):
                                    speed = clampSpeed(s)
                                    heading = clampHeading(self.robot.heading)
                                    dir = SyncsDir.backward
                                    seconds = msToSeconds(durationMs)
                                    shouldRoll = true
                                    
                                case .turn(let headingDeg, let durationMs):
                                    // Simple turning command: speed 0 towards heading.
                                    // (The actual behavior depends on device firmware.)
                                    speed = clampSpeed(0)
                                    heading = clampHeading(headingDeg)
                                    dir = SyncsDir.forward
                                    seconds = msToSeconds(durationMs)
                                    shouldRoll = true
                                    
                                case .stop:
                                    heading = clampHeading(self.robot.heading)
                                    shouldStop = true
                                    
                                case .setLED(let c):
                                    color = SyncsColor(red: c.r, green: c.g, blue: c.b)
                                    shouldSetLED = true
                                    
                                case .vibrate(let durationS):
                                    seconds = max(1, durationS)
                                    shouldVibrate = true
                                    
                                case .spin(let durationS):
                                    seconds = max(1, durationS)
                                    shouldSpin = true
                                }
                                
                                // Write Pappe vars
                                val.cmdSpeed = speed
                                val.cmdHeading = heading
                                val.cmdDir = dir
                                val.cmdSeconds = seconds
                                val.cmdColor = color
                                
                                val.doRollForSeconds = shouldRoll
                                val.doStop = shouldStop
                                val.doSetLED = shouldSetLED
                                val.doVibrate = shouldVibrate
                                val.doSpin = shouldSpin
                                
                                // Consume command
                                self.pendingCommand = nil
                            }
                            
                            //------------------------------------------------------
                            // 2) PAPPE execution (no Swift here)
                            //------------------------------------------------------
                            
                            `if` { val.doRollForSeconds as Bool } then: {
                                run(Syncs.RollForSeconds, [
                                    val.cmdSpeed,
                                    val.cmdHeading,
                                    val.cmdDir,
                                    val.cmdSeconds
                                ])
                            }
                            
                            `if` { val.doStop as Bool } then: {
                                run(Syncs.StopRoll, [
                                    val.cmdHeading
                                ])
                            }
                            
                            `if` { val.doSetLED as Bool } then: {
                                run(Syncs.SetMainLED, [val.cmdColor])
                            }
                            
                            `if` { val.doVibrate as Bool } then: {
                                exec { ctx.logInfo("Vibrate START") }
                                // Stronger vibration: Max speed and longer duration for "larger gestures"
                                // Loop frequency: 150ms + 150ms = 300ms per cycle (approx 3.3 Hz)
                                // Total duration `val.cmdSeconds`.
                                exec { val.counter = (val.cmdSeconds as Int) * 4 } 
                                
                                `repeat` {
                                    // Forward FULL POWER
                                    run(Syncs.Roll, [SyncsSpeed(255), val.cmdHeading, SyncsDir.forward])
                                    run(Syncs.WaitMilliseconds, [150])
                                    
                                    // Backward FULL POWER
                                    run(Syncs.Roll, [SyncsSpeed(255), val.cmdHeading, SyncsDir.backward])
                                    run(Syncs.WaitMilliseconds, [150])
                                    
                                    exec { val.counter = (val.counter as Int) - 1 }
                                } until: { (val.counter as Int) <= 0 }
                                
                                run(Syncs.StopRoll, [val.cmdHeading])
                                exec { ctx.logInfo("Vibrate END") }
                            }
                            
                            `if` { val.doSpin as Bool } then: {
                                exec { ctx.logInfo("Spin START") }
                                // Spin logic: Rotate 360 degrees multiple times
                                // Strategy: full speed forward while drastically changing heading
                                // Since we can't drive two motors independently easily in Syncs, we rotate the heading.
                                // We'll update heading by 90 degrees every 50ms to create a fast spin effect.
                                
                                exec { val.counter = (val.cmdSeconds as Int) * 20 }
                                
                                `repeat` {
                                    exec {
                                        // Increment heading by 45 degrees
                                        let h = (val.cmdHeading as UInt16) + 20
                                        val.cmdHeading = SyncsHeading(h % 360)
                                    }
                                    
                                    // Roll with speed 0 (just turn) or >0 to drift? 
                                    // Try speed 0 for pure rotation if robot supports pivot.
                                    // RVR supports pivot on speed 0.
                                    run(Syncs.Roll, [SyncsSpeed(0), val.cmdHeading, SyncsDir.forward])
                                    run(Syncs.WaitMilliseconds, [50])
                                    
                                    exec { val.counter = (val.counter as Int) - 1 }
                                } until: { (val.counter as Int) <= 0 }
                                
                                run(Syncs.StopRoll, [val.cmdHeading])
                                exec { ctx.logInfo("Spin END") }
                            }
                            
                            //------------------------------------------------------
                            // 3) Loop pacing
                            //------------------------------------------------------
                            run(Syncs.WaitMilliseconds, [10])
                            
                        } until: { false }
                    }
                }
            }
        }

        //------------------------------------------------------
        // 3) Start
        //------------------------------------------------------
        controller?.start()
    }

    // MARK: - Disconnect

    func disconnect() {
        controller?.stop()
        controller = nil
    }

    // MARK: - Commands

    func send(_ command: RobotCommand) {
        pendingCommand = command
    }
}
