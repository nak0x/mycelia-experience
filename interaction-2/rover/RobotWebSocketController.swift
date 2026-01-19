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
    
    init(robot: Robot, wsManager: WebSocketManager) {
        self.robot = robot
        self.wsManager = wsManager
        
        self.listenerId = wsManager.addListener { [weak self] frame in
            self?.handleFrame(frame)
        }
        
        // robot.onImpact = { [weak self] in
        //     self?.sendImpactFrame()
        // }

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
                DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self] in
                    print("🚀 Activation du Rover après délai (Scenario Interaction 2)")
                    self?.robot.forward(speed: 90, durationS: 6)
                }
            } else {
                print("⚠️ Commande ignorée pour cet ID: \(wsManager.deviceId)")
            }

        case "02-rover-toggle":
            if wsManager.deviceId == "IOS-020101" {
                print("🚀 Activation immédiate du Rover (Scenario Interaction 2)")
                robot.forward(speed: 90, durationS: 6)
            } else {
                print("⚠️ Commande ignorée pour cet ID: \(wsManager.deviceId)")
            }
            
        case "02-grass-increment":
            if robot.bluetoothName == "SB-0994" {
                print("⚖️ [Vibrate Sequence] SB-0994")
                robot.vibrate(durationS: 10)
            }

        case "02-water-flow-toggle":
            if case .bool(let val) = frame.value, val == true {
                if robot.bluetoothName == "SB-6C4C" {
                    print("⚖️ [Balance Sequence] SB-6C4C: Waiting 2s before move")
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
                         print("➡️ [Balance Sequence] SB-6C4C: Moving forward")
                         self?.robot.forward(speed: 60, durationS: 4)
                    }
                }
                else if robot.bluetoothName == "SB-42C1" {
                    print("⚖️ [Balance Sequence] SB-42C1: Waiting 12s before move")
                    DispatchQueue.main.asyncAfter(deadline: .now() + 13) { [weak self] in
                        print("➡️ [Balance Sequence] SB-42C1: Moving forward")
                        self?.robot.forward(speed: 60, durationS: 7)
                    }
                }
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
