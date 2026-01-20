//
//  WebsocketSpheroView.swift
//  IOTTools
//
//  Created by Emmanuel Moulin on 29/11/2025.
//  Redesigned by Antigravity on 18/12/2025
//

import SwiftUI

struct WebsocketSpheroView: View {
    
    // MARK: - State
    @State private var serverURL: String = "ws://192.168.10.163:8000/ws" //ws://mycelia.kibishi47.ovh/ws
    @State private var deviceId: String = "IOS-020201" // ID du sphero
    @State private var newRobotId: String = "SB-0994"
    
    @State private var wsManager: WebSocketManager?
    @State private var robotSessions: [RobotSession] = []
    
    @State private var showLogs: Bool = false
    @State private var showAddSheet: Bool = false
    
    // Known Spheros
    let knownSpheros = ["SB-0994", "SB-6C4C", "SB-42C1", "SB-F682"]
    
    // Grid Setup
    let columns = [
        GridItem(.adaptive(minimum: 300, maximum: 500), spacing: 20)
    ]
    
    // MARK: - Body
    
    var body: some View {
        ZStack {
            NeonTheme.bgMain.ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 24) {
                    
                    // ===== HEADER =====
                    headerView
                    
                    // ===== DASHBOARD GRID =====
                    LazyVGrid(columns: columns, spacing: 20) {
                        
                        // WebSocket Status Card
                        webSocketCard
                        
                        // Robot Cards
                        ForEach(robotSessions.indices, id: \.self) { index in
                            robotCard(for: index)
                        }
                        
                        // Add New Robot Card
                        addRobotButtonCard
                    }
                    .padding()
                    
                    // ===== LOGS SECTION =====
                    logsSection
                    
                    Spacer(minLength: 50)
                }
                .padding(.top)
            }
        }
        .sheet(isPresented: $showAddSheet) {
            addRobotSheet
        }
    }
    
    // MARK: - Subviews
    
    var headerView: some View {
        HStack {
            VStack(alignment: .leading) {
                Text("SPHERO COMMAND")
                    .font(.caption)
                    .tracking(2)
                    .foregroundColor(NeonTheme.accentCyan)
                
                Text("Sphero Swarm")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.white)
            }
            
            Spacer()
            
            // Connection Status Badge
            HStack {
                Circle()
                    .fill(wsManager?.isConnected == true ? NeonTheme.accentCyan : Color.red)
                    .frame(width: 8, height: 8)
                    .shadow(color: wsManager?.isConnected == true ? NeonTheme.accentCyan : .clear, radius: 5)
                
                Text(wsManager?.isConnected == true ? "ONLINE" : "OFFLINE")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color.white.opacity(0.1))
            .cornerRadius(20)
        }
        .padding(.horizontal)
    }
    
    var webSocketCard: some View {
        NeonCard(borderColor: NeonTheme.accentPurple) {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Image(systemName: "server.rack")
                        .foregroundColor(NeonTheme.accentPurple)
                    Text("Gateway Connection")
                        .font(.headline)
                        .foregroundColor(.white)
                    Spacer()
                }
                
                CustomTextField(text: $serverURL, placeholder: "ws://localhost:8000/ios", bg: NeonTheme.bgInput, color: .white)
                
                CustomTextField(text: $deviceId, placeholder: "IOS-ID", bg: NeonTheme.bgInput, color: .white)
                
                GlowingButton(
                    title: wsManager?.isConnected == true ? "Connected" : "Connect Gateway",
                    icon: wsManager?.isConnected == true ? "checkmark.shield.fill" : "network",
                    color: NeonTheme.accentPurple,
                    action: toggleWebSocket,
                    isActive: wsManager?.isConnected == true
                )
            }
        }
    }
    
    func robotCard(for index: Int) -> some View {
        // Safe check
        guard index < robotSessions.count else { return AnyView(EmptyView()) }

        let session = robotSessions[index]
        let isConnected = session.isConnected
        let robot = session.robot as? Sphero
        
        return AnyView(NeonCard(borderColor: isConnected ? NeonTheme.accentPink : Color.gray) {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Image(systemName: "circle.circle.fill")
                        .foregroundColor(isConnected ? NeonTheme.accentPink : .gray)
                        .font(.title3)
                    
                    VStack(alignment: .leading) {
                        Text(session.targetDeviceId)
                            .font(.headline)
                            .foregroundColor(.white)
                        Text(isConnected ? "Sphero Active" : "Disconnected")
                            .font(.caption)
                            .foregroundColor(isConnected ? NeonTheme.accentPink : .gray)
                    }
                    
                    Spacer()
                    
                    Button(action: { removeRobot(at: index) }) {
                        Image(systemName: "xmark")
                            .foregroundColor(.gray)
                            .padding(8)
                    }
                }
                
                Divider().background(Color.white.opacity(0.1))
                
                // SPHERO SPECIFIC STATS
                if isConnected {
                    HStack(spacing: 20) {
                        StatCircle(value: "\(robot?.impactCount ?? 0)", label: "IMPACTS", color: NeonTheme.accentRed)
                        
                        let velocity = sqrt(pow(robot?.lastSample.vx ?? 0, 2) + pow(robot?.lastSample.vy ?? 0, 2)) * 100
                        StatCircle(value: String(format: "%.0f", velocity), label: "CM/S", color: NeonTheme.accentYellow)
                        
                        StatCircle(value: "100%", label: "BATTERY", color: .green)
                        
                        Spacer()
                    }
                } else {
                    Text("Waiting for connection...")
                        .font(.caption)
                        .italic()
                        .foregroundColor(.gray)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.vertical, 12)
                }
                
                // CONTROLS
                HStack(spacing: 12) {
                    if !isConnected {
                        GlowingButton(
                            title: "Connect",
                            icon: "link",
                            color: NeonTheme.accentPink,
                            action: { connectRobot(at: index) }
                        )
                    } else {
                        VStack(spacing: 12) {
                            // 1. Connection
                            GlowingButton(
                                title: "Disconnect",
                                icon: "link.badge.plus",
                                color: NeonTheme.accentPurple,
                                action: { disconnectRobot(at: index) }
                            )
                            
                            Divider().background(Color.white.opacity(0.1))
                            
                            // 2. LED Controls
                            HStack {
                                Text("LED")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundColor(.gray)
                                Spacer()
                                ColorButton(color: .red, action: { robot?.setMainLED(color: .red) })
                                ColorButton(color: .green, action: { robot?.setMainLED(color: .green) })
                                ColorButton(color: .blue, action: { robot?.setMainLED(color: .blue) })
                                ColorButton(color: .white, action: { robot?.setMainLED(color: .white) })
                                ColorButton(color: .black, action: { robot?.setMainLED(color: .off) })
                            }
                            
                            Divider().background(Color.white.opacity(0.1))
                            
                            // 3. Movement / Actions
                            HStack {
                                // Direction Arrows (Mini d-pad)
                                HStack(spacing: 2) {
                                    Button(action: { robot?.turn(degrees: -45) }) {
                                        Image(systemName: "arrow.counterclockwise")
                                            .padding(6)
                                            .background(Color.white.opacity(0.1))
                                            .cornerRadius(4)
                                    }
                                    
                                    Button(action: { robot?.forward(speed: 60) }) {
                                        Image(systemName: "arrow.up")
                                            .padding(6)
                                            .background(Color.white.opacity(0.1))
                                            .cornerRadius(4)
                                    }
                                    
                                    Button(action: { robot?.spin(durationS: 5) }) {
                                        Image(systemName: "arrow.triangle.2.circlepath")
                                            .padding(6)
                                            .background(NeonTheme.accentCyan.opacity(0.3))
                                            .cornerRadius(4)
                                    }
                                }
                                .font(.caption)
                                .foregroundColor(.white)
                                
                                Spacer()
                                
                                // Vibrate Action
                                Button(action: { robot?.vibrate(durationS: 10) }) {
                                    HStack(spacing: 4) {
                                        Image(systemName: "waveform.path.ecg")
                                        Text("VIB 10s")
                                    }
                                    .font(.system(size: 10, weight: .bold))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(NeonTheme.accentYellow.opacity(0.2))
                                    .foregroundColor(NeonTheme.accentYellow)
                                    .cornerRadius(4)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 4)
                                            .stroke(NeonTheme.accentYellow, lineWidth: 1)
                                    )
                                }
                            }
                        }
                    }
                }
            }
        })
    }
    
    var addRobotButtonCard: some View {
        Button(action: { showAddSheet.toggle() }) {
            ZStack {
                RoundedRectangle(cornerRadius: 20)
                    .stroke(style: StrokeStyle(lineWidth: 2, dash: [10]))
                    .foregroundColor(Color.white.opacity(0.1))
                
                VStack(spacing: 8) {
                    Image(systemName: "plus")
                        .font(.largeTitle)
                        .foregroundColor(NeonTheme.accentYellow)
                    
                    Text("Add Sphero")
                        .fontWeight(.semibold)
                        .foregroundColor(NeonTheme.textSecondary)
                }
            }
            .frame(minHeight: 200)
        }
    }
    
    var logsSection: some View {
        VStack {
            if let ws = wsManager {
                Button(action: { withAnimation { showLogs.toggle() } }) {
                    HStack {
                        Text("SYSTEM LOGS")
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundColor(NeonTheme.textSecondary)
                        Spacer()
                        Image(systemName: showLogs ? "chevron.up" : "chevron.down")
                            .foregroundColor(NeonTheme.textSecondary)
                    }
                    .padding(.horizontal)
                }
                
                if showLogs {
                    NeonCard {
                        ScrollView {
                            VStack(alignment: .leading, spacing: 4) {
                                ForEach(Array(ws.logs.enumerated()), id: \.offset) { index, log in
                                    Text(log)
                                        .font(.system(size: 10, design: .monospaced))
                                        .foregroundColor(NeonTheme.textSecondary)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                }
                            }
                        }
                        .frame(height: 150)
                        
                        HStack {
                            Spacer()
                            Button("Clear logs") { wsManager?.clearLogs() }
                                .font(.caption)
                                .foregroundColor(NeonTheme.accentPink)
                        }
                    }
                    .padding(.horizontal)
                }
            }
        }
    }
    
    var addRobotSheet: some View {
        ZStack {
            NeonTheme.bgMain.ignoresSafeArea()
            
            VStack(spacing: 24) {
                Text("Add Sphero")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                
                Menu {
                    ForEach(knownSpheros, id: \.self) { sphero in
                        Button(sphero) {
                            newRobotId = sphero
                        }
                    }
                } label: {
                    HStack {
                        Text(newRobotId.isEmpty ? "Select Sphero" : newRobotId)
                            .foregroundColor(.white)
                        Spacer()
                        Image(systemName: "chevron.down")
                            .foregroundColor(.white.opacity(0.6))
                    }
                    .padding()
                    .background(NeonTheme.bgInput)
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.white.opacity(0.1), lineWidth: 1)
                    )
                }
                .padding()
                
                GlowingButton(
                    title: "Add to Swarm",
                    icon: "plus.circle.fill",
                    color: NeonTheme.accentYellow,
                    action: {
                        addNewRobotSession(id: newRobotId)
                        showAddSheet = false
                    }
                )
                .padding()
                
                Spacer()
            }
            .padding()
        }
    }
    
    // MARK: - Logic
    
    private func toggleWebSocket() {
        if wsManager?.isConnected == true {
            disconnectWebSocket()
        } else {
            connectWebSocket()
        }
    }
    
    private func connectWebSocket() {
        wsManager?.disconnect()
        let newManager = WebSocketManager(serverURL: serverURL, deviceId: deviceId)
        setupWSCallbacks(newManager)
        self.wsManager = newManager
        newManager.connect()
        refreshAllBridges()
    }
    
    private func disconnectWebSocket() {
        wsManager?.disconnect()
        for i in robotSessions.indices {
            robotSessions[i].controller = nil
        }
        wsManager = nil
    }
    
    private func addNewRobotSession(id: String) {
        let session = RobotSession(targetDeviceId: id)
        robotSessions.append(session)
    }
    
    private func removeRobot(at index: Int) {
        robotSessions[index].robot?.disconnect()
        robotSessions.remove(at: index)
    }
    
    private func connectRobot(at index: Int) {
        let targetId = robotSessions[index].targetDeviceId
        let newRobot = Sphero(bluetoothName: targetId)
        
        // Setup Callbacks
        // Fix for Reactivity
        newRobot.onConnect = {
            print("[\(targetId)] Connected")
            DispatchQueue.main.async {
                if index < self.robotSessions.count {
                    var session = self.robotSessions[index]
                    session.robot = newRobot
                    self.robotSessions[index] = session
                    self.attemptBridge(at: index)
                }
            }
        }
        
        newRobot.onDisconnect = {
            print("[\(targetId)] Disconnected")
            DispatchQueue.main.async {
                if index < self.robotSessions.count {
                    self.robotSessions[index] = self.robotSessions[index] // Trigger update
                }
            }
        }
        
        robotSessions[index].robot = newRobot
        newRobot.connect()
    }
    
    private func disconnectRobot(at index: Int) {
        robotSessions[index].controller = nil
        robotSessions[index].robot?.disconnect()
    }
    
    private func attemptBridge(at index: Int) {
        guard let ws = wsManager, ws.isConnected else { return }
        if let r = robotSessions[index].robot, r.isConnected {
             robotSessions[index].controller = RobotWebSocketController(robot: r, wsManager: ws)
        }
    }
    
    private func refreshAllBridges() {
        guard let ws = wsManager, ws.isConnected else { return }
        
        for i in robotSessions.indices {
            if let r = robotSessions[i].robot, r.isConnected {
                robotSessions[i].controller = RobotWebSocketController(robot: r, wsManager: ws)
            }
        }
    }
    
    private func setupWSCallbacks(_ manager: WebSocketManager) {
        manager.onConnectionChanged = { isConnected in
            if !isConnected {
                 // Break all bridges
                 for i in 0..<self.robotSessions.count {
                     self.robotSessions[i].controller = nil
                 }
            } else {
                self.refreshAllBridges()
            }
        }
    }
}

struct ColorButton: View {
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Circle()
                .fill(color)
                .frame(width: 20, height: 20)
                .overlay(
                    Circle()
                        .stroke(Color.white.opacity(0.5), lineWidth: 1)
                )
        }
    }
}

#Preview {
    WebsocketSpheroView()
}
