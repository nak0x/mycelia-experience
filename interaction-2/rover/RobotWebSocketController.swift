//
//  RobotWebSocketController.swift
//  IOTTools
//
//  Created by Jocelyn Marcilloux-Buisson on 15/12/2025.
//

import Foundation

class RobotWebSocketController {
    
    private let robot: Robot
    private let wsManager: WebSocketManager
    private var listenerId: UUID?

    private var sphero1: String = "SB-92B2"
    private var sphero2: String = "SB-F682"
    private var sphero3: String = "SB-42C1"
    
    public var spheroNumber: Int?
    
    init(robot: Robot, wsManager: WebSocketManager) {
        self.robot = robot
        self.wsManager = wsManager
        
        // Inline initialization handles sphero1, sphero2, sphero3
        // spheroNumber is optional, defaults to nil
        
        if robot.bluetoothName == "SB-92B2" { self.spheroNumber = 1 }
        else if robot.bluetoothName == "SB-F682" { self.spheroNumber = 2 }
        else if robot.bluetoothName == "SB-42C1" { self.spheroNumber = 3 }
        
        // Setup listener last to avoid capturing self before full initialization
        self.listenerId = wsManager.addListener { [weak self] frame in
            self?.handleFrame(frame)
        }
        
        sendNewConnection()
    }
    
    deinit {
        if let id = listenerId {
            wsManager.removeListener(id)
        }
    }

    private func sendNewConnection() {
        guard robot.isConnected else { return }
        
        let frame = Frame(
            senderId: wsManager.deviceId,
            action: "00-new-connection",
            value: .null
        )
        
        wsManager.sendFrame(frame)
        print("🚀 Connexion établie avec le server")
    }
    
    // private func sendImpactFrame() {
    //     guard robot.isConnected else { return }
        
    //     let frame = Frame(
    //         senderId: wsManager.deviceId,
    //         action: "02-sphero-impact",
    //         value: .bool(true)
    //     )
        
    //     wsManager.sendFrame(frame)
    //     print("💥 Impact envoyé via WebSocket")
    // }

    private func sendInteractonDoneFrame() {
        guard robot.isConnected else { return }
        
        let frame = Frame(
            senderId: wsManager.deviceId,
            action: "02-interaction-done",
            value: .bool(true)
        )
        
        wsManager.sendFrame(frame)
        print("🚀 Interaction terminée via WebSocket")
    }
    
    private func handleFrame(_ frame: Frame) {
        guard robot.isConnected else {
            print("⚠️ Robot non connecté, commande ignorée")
            return
        }
        
        print("🎮 Commande reçue: \(frame.action) = \(frame.value.anyValue)")
        
        switch frame.action {
            
        // ===== MOUVEMENTS =====
        case "forward":
            if let params = frame.value.intArrayValue, !params.isEmpty {
                let speed = params[0]
                let duration = params.count > 1 ? params[1] : 1
                robot.forward(speed: speed, durationS: duration)
            }
            else if let speed = frame.value.intValue {
                robot.forward(speed: speed, durationS: 1)
            }
            
        case "backward":
            if let params = frame.value.intArrayValue, !params.isEmpty {
                let speed = params[0]
                let duration = params.count > 1 ? params[1] : 1
                robot.backward(speed: speed, durationS: duration)
            }
            else if let speed = frame.value.intValue {
                robot.backward(speed: speed, durationS: 1)
            }
            
        case "turn":
            if let degrees = frame.value.intValue {
                robot.turn(degrees: degrees)
            }
            
        case "stop":
            robot.stop()
            
        case "heading":
            if let heading = frame.value.intValue {
                robot.heading = heading
            }
            
        // ===== LED =====
        case "led":
            if let colorData = frame.value.stringValue {
                let components = colorData.split(separator: ",").compactMap { UInt8($0) }
                if components.count == 3 {
                    let color = RobotColor(r: components[0], g: components[1], b: components[2])
                    robot.setMainLED(color: color)
                }
            }
            
        case "led-red":   robot.setMainLED(color: .red)
        case "led-green": robot.setMainLED(color: .green)
        case "led-blue":  robot.setMainLED(color: .blue)
        case "led-white": robot.setMainLED(color: .white)
        case "led-off":   robot.setMainLED(color: .off)
            
        // ===== INTERACTION 2 SCENARIO =====
        case "01-interaction-done":
            if wsManager.deviceId == "IOS-020101" {
                print("⏳ Début du délai de 10s avant activation...")
                DispatchQueue.main.asyncAfter(deadline: .now() + 15) { [weak self] in
                    print("🚀 Activation du Rover après délai (Scenario Interaction 2)")
                    self?.robot.forward(speed: 90, durationS: 7)
                }
            } else {
                print("⚠️ Commande ignorée pour cet ID: \(wsManager.deviceId)")
            }

        case "02-rover-toggle":
            if wsManager.deviceId == "IOS-020101" {
                print("🚀 Activation immédiate du Rover (Scenario Interaction 2)")
                robot.forward(speed: 90, durationS: 7)
            } else {
                print("⚠️ Commande ignorée pour cet ID: \(wsManager.deviceId)")
            }
            
        case "02-grass-increment":
            if robot.bluetoothName == self.sphero1 {
                print("⚖️ [Vibrate Sequence] - ", self.sphero1)
                robot.vibrate(durationS: 3)
            }

        case "02-water-flow-toggle":
            if case .bool(let val) = frame.value, val == true {
                if robot.bluetoothName == self.sphero2 {
                    print("⚖️ [Earth Sequence] -", self.sphero2)
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
                         print("➡️ [Earth Sequence] - ", self?.sphero2, " - Moving forward")
                         self?.robot.forward(speed: 50, durationS: 3)
                    }
                    
                    // Only this robot sends the done frame to avoid duplicates
                    DispatchQueue.main.asyncAfter(deadline: .now() + 15) { [weak self] in
                        self?.sendInteractonDoneFrame()
                    }
                }
                else if robot.bluetoothName == self.sphero3 {
                    print("⚖️ [Balance Sequence] - ", self.sphero3)
                    DispatchQueue.main.asyncAfter(deadline: .now() + 13) { [weak self] in
                        print("➡️ [Balance Sequence] -", self?.sphero3, " - Moving forward")
                        self?.robot.forward(speed: 60, durationS: 6)
                    }
                }
            }
        
        case "02-sphero-02-forward":
            if robot.bluetoothName == self.sphero2 {
                print("⚖️ [Vibrate Sequence] - ", self.sphero2)
                robot.forward(speed: 60, durationS: 2)
            }
        
        case "02-sphero-03-forward":
            if robot.bluetoothName == self.sphero3 {
                print("⚖️ [Vibrate Sequence] - ", self.sphero3)
                robot.forward(speed: 60, durationS: 6)
            }
            
        default:
            print("⚠️ Commande inconnue ou mal formatée: \(frame.action)")
        }
    }
    
    func sendRobotState() {
        guard robot.isConnected else { return }
        
        let stateDict: [String: FrameValue] = [
            "robot-connected": .bool(robot.isConnected),
            "robot-heading": .int(robot.heading),
            "robot-battery": .string(robot.batteryState.description),
            "robot-x": .float(Double(robot.lastSample.x)),
            "robot-y": .float(Double(robot.lastSample.y)),
            "robot-yaw": .float(Double(robot.lastSample.yaw))
        ]
        
        let frame = Frame(
            senderId: wsManager.deviceId,
            action: "robot-state",
            value: .dictionary(stateDict)
        )
        
        wsManager.sendFrame(frame)
    }
}

extension BatteryState: CustomStringConvertible {
    public var description: String {
        switch self {
        case .ok: return "ok"
        case .low: return "low"
        case .critical: return "critical"
        case .unknown: return "unknown"
        }
    }
}
