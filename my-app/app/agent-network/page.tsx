"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Bot, Brain, Shield, Target, TrendingUp, Activity, MessageSquare, Settings, Send, User } from "lucide-react"

export default function AgentNetwork() {
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm your AI Trading Assistant. I can coordinate with all our specialized agents to help you with trading decisions, market analysis, and portfolio management. How can I help you today?",
      timestamp: new Date().toLocaleTimeString(),
    },
  ])
  const [chatInput, setChatInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)

  // MOCK DATA - Replace with actual backend integration
  // Connect to: /agents/status endpoint from your FastAPI backend
  const [agents, setAgents] = useState([
    {
      id: "macro-analyst",
      name: "Macro Analyst",
      type: "Economic Analysis",
      status: "active",
      confidence: 87,
      lastDecision: "2 min ago",
      decisions: 156,
      accuracy: 73.2,
      currentTask: "Analyzing Fed policy impact on tech sector",
      icon: Brain,
      color: "blue",
      // BACKEND INTEGRATION: Connect to agents/macro_analyst.py
      // API endpoint: /agents/macro-analyst/status
      // WebSocket: /ws/agents/macro-analyst for real-time updates
    },
    {
      id: "quant-research",
      name: "Quant Research",
      type: "Strategy Development",
      status: "active",
      confidence: 92,
      lastDecision: "5 min ago",
      decisions: 89,
      accuracy: 81.7,
      currentTask: "Backtesting momentum strategy variations",
      icon: TrendingUp,
      color: "emerald",
      // BACKEND INTEGRATION: Connect to agents/quant_researcher.py
      // API endpoint: /agents/quant-research/status
      // WebSocket: /ws/agents/quant-research for real-time updates
    },
    {
      id: "risk-manager",
      name: "Risk Manager",
      type: "Portfolio Protection",
      status: "monitoring",
      confidence: 95,
      lastDecision: "1 min ago",
      decisions: 234,
      accuracy: 88.9,
      currentTask: "Monitoring portfolio correlation risk",
      icon: Shield,
      color: "red",
      // BACKEND INTEGRATION: Connect to agents/risk_manager.py
      // API endpoint: /agents/risk-manager/status
      // WebSocket: /ws/agents/risk-manager for real-time updates
    },
    {
      id: "execution-agent",
      name: "Execution Agent",
      type: "Trade Execution",
      status: "active",
      confidence: 89,
      lastDecision: "30 sec ago",
      decisions: 412,
      accuracy: 76.4,
      currentTask: "Executing AAPL position adjustment",
      icon: Target,
      color: "purple",
      // BACKEND INTEGRATION: Connect to agents/execution_agent.py
      // API endpoint: /agents/execution-agent/status
      // WebSocket: /ws/agents/execution-agent for real-time updates
    },
  ])

  // MOCK DATA - Replace with actual backend integration
  // Connect to: /agents/conversations endpoint from your FastAPI backend
  const [conversations, setConversations] = useState([
    {
      agent: "Risk Manager",
      message: "Portfolio beta increased to 1.3. Recommend reducing tech exposure by 15%.",
      timestamp: "2 min ago",
      priority: "high",
      // BACKEND INTEGRATION: Real-time agent communications via WebSocket
      // WebSocket endpoint: /ws/agent-communications
    },
    {
      agent: "Macro Analyst",
      message: "Fed dovish signals detected. Increasing growth stock allocation confidence to 85%.",
      timestamp: "8 min ago",
      priority: "medium",
    },
    {
      agent: "Execution Agent",
      message: "Successfully executed NVDA buy order. Filled at $925.75, 2% below target.",
      timestamp: "12 min ago",
      priority: "low",
    },
    {
      agent: "Quant Research",
      message: "New momentum signal generated for TSLA. Backtested Sharpe ratio: 2.1",
      timestamp: "15 min ago",
      priority: "medium",
    },
  ])

  // BACKEND INTEGRATION: Replace with actual API calls
  useEffect(() => {
    // TODO: Replace with WebSocket connection to /ws/agents/status
    const interval = setInterval(() => {
      setAgents((prev) =>
        prev.map((agent) => ({
          ...agent,
          confidence: Math.max(70, Math.min(98, agent.confidence + (Math.random() - 0.5) * 4)),
          decisions: agent.status === "active" ? agent.decisions + Math.floor(Math.random() * 2) : agent.decisions,
        })),
      )
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // CHATBOT FUNCTIONS - Connect to your main AI orchestrator
  const handleSendMessage = async () => {
    if (!chatInput.trim()) return

    const userMessage = {
      role: "user",
      content: chatInput,
      timestamp: new Date().toLocaleTimeString(),
    }

    setChatMessages((prev) => [...prev, userMessage])
    setChatInput("")
    setIsTyping(true)

    // BACKEND INTEGRATION: Replace with actual API call to your main AI orchestrator
    // API endpoint: /chat/orchestrator
    // This should connect to your main agent that can coordinate with all sub-agents
    try {
      // TODO: Replace with actual API call
      // const response = await fetch('/api/chat/orchestrator', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     message: chatInput,
      //     available_agents: agents.map(a => a.id),
      //     context: 'agent_network_dashboard'
      //   })
      // })
      // const data = await response.json()

      // MOCK RESPONSE - Replace with actual backend response
      setTimeout(() => {
        const mockResponse = {
          role: "assistant",
          content: `I've analyzed your request "${chatInput}". Based on current market conditions, I'm coordinating with our Risk Manager and Macro Analyst to provide you with the best recommendation. The Risk Manager suggests maintaining current position sizes while the Macro Analyst indicates favorable conditions for tech sector exposure.`,
          timestamp: new Date().toLocaleTimeString(),
          agents_consulted: ["risk-manager", "macro-analyst"], // This should come from backend
        }
        setChatMessages((prev) => [...prev, mockResponse])
        setIsTyping(false)
      }, 2000)
    } catch (error) {
      console.error("Chat error:", error)
      setIsTyping(false)
    }
  }

  // AGENT INTERACTION FUNCTIONS
  const handleViewDetails = (agent) => {
    setSelectedAgent(agent)
    // BACKEND INTEGRATION: Fetch detailed agent data
    // API endpoint: /agents/{agent.id}/details
  }

  const handleChatWithAgent = (agent) => {
    // BACKEND INTEGRATION: Start direct conversation with specific agent
    // API endpoint: /agents/{agent.id}/chat
    // WebSocket: /ws/agents/{agent.id}/chat
    console.log(`Starting chat with ${agent.name}`)
    // TODO: Implement direct agent chat functionality
  }

  const handleConfigureAgents = () => {
    // BACKEND INTEGRATION: Open agent configuration
    // API endpoint: /agents/config
    console.log("Opening agent configuration")
    // TODO: Implement agent configuration modal/page
  }

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-full overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-wider">AI AGENT NETWORK</h1>
          <p className="text-sm text-neutral-400">Monitor autonomous trading agents and their decisions</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleConfigureAgents} className="bg-emerald-500 hover:bg-emerald-600 text-white text-sm">
            <Settings className="w-4 h-4 mr-2" />
            Configure Agents
          </Button>
        </div>
      </div>

      {/* Agent Overview Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs text-neutral-400 tracking-wider">ACTIVE AGENTS</p>
                <p className="text-xl sm:text-2xl font-bold text-emerald-400 font-mono">
                  {agents.filter((a) => a.status === "active").length}
                </p>
              </div>
              <Bot className="w-6 h-6 sm:w-8 sm:h-8 text-emerald-400 flex-shrink-0" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs text-neutral-400 tracking-wider">AVG CONFIDENCE</p>
                <p className="text-xl sm:text-2xl font-bold text-white font-mono">
                  {Math.round(agents.reduce((sum, a) => sum + a.confidence, 0) / agents.length)}%
                </p>
              </div>
              <Brain className="w-6 h-6 sm:w-8 sm:h-8 text-blue-400 flex-shrink-0" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs text-neutral-400 tracking-wider">DECISIONS TODAY</p>
                <p className="text-xl sm:text-2xl font-bold text-white font-mono">
                  {agents.reduce((sum, a) => sum + a.decisions, 0)}
                </p>
              </div>
              <Activity className="w-6 h-6 sm:w-8 sm:h-8 text-purple-400 flex-shrink-0" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <p className="text-xs text-neutral-400 tracking-wider">AVG ACCURACY</p>
                <p className="text-xl sm:text-2xl font-bold text-white font-mono">
                  {(agents.reduce((sum, a) => sum + a.accuracy, 0) / agents.length).toFixed(1)}%
                </p>
              </div>
              <Target className="w-6 h-6 sm:w-8 sm:h-8 text-orange-400 flex-shrink-0" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* MAIN AI ORCHESTRATOR CHATBOT */}
      {/* BACKEND INTEGRATION: Connect to your main AI orchestrator from /orchestrator/main.py */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-emerald-400 flex items-center gap-2">
            <Bot className="w-5 h-5" />
            AI Trading Assistant
            <Badge variant="outline" className="ml-auto text-xs border-emerald-500 text-emerald-400">
              ORCHESTRATOR
            </Badge>
          </CardTitle>
          <p className="text-sm text-neutral-400">Chat with the main AI that coordinates all trading agents</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Chat Messages Area */}
          <ScrollArea className="h-64 w-full rounded border border-neutral-800 bg-neutral-950 p-4">
            <div className="space-y-4">
              {chatMessages.map((message, index) => (
                <div key={index} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`flex gap-3 max-w-[80%] ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.role === "user" ? "bg-blue-500" : "bg-emerald-500"
                      }`}
                    >
                      {message.role === "user" ? (
                        <User className="w-4 h-4 text-white" />
                      ) : (
                        <Bot className="w-4 h-4 text-white" />
                      )}
                    </div>
                    <div
                      className={`rounded-lg p-3 ${
                        message.role === "user" ? "bg-blue-600 text-white" : "bg-neutral-800 text-neutral-200"
                      }`}
                    >
                      <p className="text-sm leading-relaxed">{message.content}</p>
                      <p className="text-xs opacity-70 mt-2">{message.timestamp}</p>
                      {message.agents_consulted && (
                        <div className="flex gap-1 mt-2">
                          {message.agents_consulted.map((agentId) => (
                            <Badge key={agentId} variant="outline" className="text-xs">
                              {agents.find((a) => a.id === agentId)?.name}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-neutral-800 rounded-lg p-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"></div>
                      <div
                        className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      ></div>
                      <div
                        className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      ></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Chat Input */}
          <div className="flex gap-2">
            <Input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Ask about market conditions, trading strategies, or agent coordination..."
              className="flex-1 bg-neutral-800 border-neutral-700 text-white placeholder:text-neutral-400 focus:border-emerald-500"
              disabled={isTyping}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || isTyping}
              className="bg-emerald-500 hover:bg-emerald-600 text-white px-4"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setChatInput("What's the current market sentiment?")}
              className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-white bg-transparent text-xs"
            >
              Market Sentiment
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setChatInput("Show me portfolio risk analysis")}
              className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-white bg-transparent text-xs"
            >
              Risk Analysis
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setChatInput("Generate new trading signals")}
              className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-white bg-transparent text-xs"
            >
              Trading Signals
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Individual Agent Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {agents.map((agent) => {
          const IconComponent = agent.icon
          return (
            <Card
              key={agent.id}
              className="bg-neutral-900 border-neutral-800 hover:border-neutral-700 transition-colors"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div
                      className={`p-2 rounded flex-shrink-0 ${
                        agent.color === "blue"
                          ? "bg-blue-500/20"
                          : agent.color === "emerald"
                            ? "bg-emerald-500/20"
                            : agent.color === "red"
                              ? "bg-red-500/20"
                              : "bg-purple-500/20"
                      }`}
                    >
                      <IconComponent
                        className={`w-5 h-5 ${
                          agent.color === "blue"
                            ? "text-blue-400"
                            : agent.color === "emerald"
                              ? "text-emerald-400"
                              : agent.color === "red"
                                ? "text-red-400"
                                : "text-purple-400"
                        }`}
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-white text-base sm:text-lg truncate">{agent.name}</CardTitle>
                      <p className="text-sm text-neutral-400 truncate">{agent.type}</p>
                    </div>
                  </div>
                  <Badge
                    variant={agent.status === "active" ? "default" : "secondary"}
                    className={`${agent.status === "active" ? "bg-emerald-500" : ""} text-xs flex-shrink-0`}
                  >
                    {agent.status.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Current Task */}
                <div>
                  <p className="text-xs text-neutral-400 mb-1">CURRENT TASK</p>
                  <p className="text-sm text-neutral-300 leading-relaxed">{agent.currentTask}</p>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-3 gap-3 sm:gap-4">
                  <div>
                    <p className="text-xs text-neutral-400 mb-1">CONFIDENCE</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-neutral-700 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${
                            agent.color === "blue"
                              ? "bg-blue-400"
                              : agent.color === "emerald"
                                ? "bg-emerald-400"
                                : agent.color === "red"
                                  ? "bg-red-400"
                                  : "bg-purple-400"
                          }`}
                          style={{ width: `${agent.confidence}%` }}
                        />
                      </div>
                      <span className="text-sm text-white font-mono flex-shrink-0">{agent.confidence}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400 mb-1">DECISIONS</p>
                    <p className="text-base sm:text-lg font-bold text-white font-mono">{agent.decisions}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400 mb-1">ACCURACY</p>
                    <p className="text-base sm:text-lg font-bold text-white font-mono">{agent.accuracy}%</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewDetails(agent)}
                    className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-white bg-transparent text-xs"
                  >
                    View Details
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleChatWithAgent(agent)}
                    className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-white bg-transparent text-xs"
                  >
                    <MessageSquare className="w-4 h-4 mr-1" />
                    Chat
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Agent Conversations */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400 flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Recent Agent Communications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {conversations.map((conv, index) => (
              <div key={index} className="p-4 bg-neutral-800 rounded">
                <div className="flex items-start justify-between mb-2 gap-2">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <Badge
                      variant="outline"
                      className={`text-xs flex-shrink-0 ${
                        conv.priority === "high"
                          ? "border-red-500 text-red-400"
                          : conv.priority === "medium"
                            ? "border-yellow-500 text-yellow-400"
                            : "border-emerald-500 text-emerald-400"
                      }`}
                    >
                      {conv.priority.toUpperCase()}
                    </Badge>
                    <span className="font-medium text-white truncate">{conv.agent}</span>
                  </div>
                  <span className="text-xs text-neutral-500 flex-shrink-0">{conv.timestamp}</span>
                </div>
                <p className="text-sm text-neutral-300 leading-relaxed">{conv.message}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="bg-neutral-900 border-neutral-800 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <div
                  className={`p-3 rounded flex-shrink-0 ${
                    selectedAgent.color === "blue"
                      ? "bg-blue-500/20"
                      : selectedAgent.color === "emerald"
                        ? "bg-emerald-500/20"
                        : selectedAgent.color === "red"
                          ? "bg-red-500/20"
                          : "bg-purple-500/20"
                  }`}
                >
                  <selectedAgent.icon
                    className={`w-6 h-6 ${
                      selectedAgent.color === "blue"
                        ? "text-blue-400"
                        : selectedAgent.color === "emerald"
                          ? "text-emerald-400"
                          : selectedAgent.color === "red"
                            ? "text-red-400"
                            : "text-purple-400"
                    }`}
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <CardTitle className="text-xl font-bold text-white truncate">{selectedAgent.name}</CardTitle>
                  <p className="text-sm text-neutral-400 truncate">{selectedAgent.type}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                onClick={() => setSelectedAgent(null)}
                className="text-neutral-400 hover:text-white flex-shrink-0"
              >
                ✕
              </Button>
            </CardHeader>
            <ScrollArea className="flex-1">
              <CardContent className="space-y-6 p-6">
                {/* Status Overview */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-neutral-400 mb-1">STATUS</p>
                    <Badge
                      variant={selectedAgent.status === "active" ? "default" : "secondary"}
                      className={selectedAgent.status === "active" ? "bg-emerald-500" : ""}
                    >
                      {selectedAgent.status.toUpperCase()}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400 mb-1">CONFIDENCE</p>
                    <p className="text-lg font-bold text-white">{selectedAgent.confidence}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400 mb-1">DECISIONS TODAY</p>
                    <p className="text-lg font-bold text-white">{selectedAgent.decisions}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400 mb-1">ACCURACY RATE</p>
                    <p className="text-lg font-bold text-white">{selectedAgent.accuracy}%</p>
                  </div>
                </div>

                {/* Current Task */}
                <div>
                  <p className="text-sm text-neutral-400 mb-2">CURRENT TASK</p>
                  <p className="text-white bg-neutral-800 p-3 rounded leading-relaxed">{selectedAgent.currentTask}</p>
                </div>

                {/* Recent Decisions - MOCK DATA */}
                <div>
                  <p className="text-sm text-neutral-400 mb-3">RECENT DECISIONS</p>
                  <div className="space-y-2">
                    {/* MOCK DATA - Replace with actual agent decision history */}
                    {/* BACKEND INTEGRATION: /agents/{agent.id}/decisions endpoint */}
                    {[
                      "Increased tech sector allocation by 5% based on earnings momentum",
                      "Reduced position size in TSLA due to elevated volatility",
                      "Generated buy signal for AAPL at support level $175",
                      "Recommended hedging strategy using VIX calls",
                    ].map((decision, idx) => (
                      <div key={idx} className="flex items-center gap-3 p-2 bg-neutral-800 rounded text-sm">
                        <div className="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0" />
                        <span className="text-neutral-300 flex-1">{decision}</span>
                        <span className="text-xs text-neutral-500 flex-shrink-0">{idx + 1}h ago</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-3 pt-4 border-t border-neutral-800">
                  <Button
                    onClick={() => handleChatWithAgent(selectedAgent)}
                    className="bg-emerald-500 hover:bg-emerald-600 text-white"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Start Conversation
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      // BACKEND INTEGRATION: Open agent configuration
                      console.log(`Configuring ${selectedAgent.name}`)
                    }}
                    className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-white bg-transparent"
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Configure Agent
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      // BACKEND INTEGRATION: View agent performance metrics
                      console.log(`Viewing performance for ${selectedAgent.name}`)
                    }}
                    className="border-neutral-700 text-neutral-400 hover:bg-neutral-800 hover:text-white bg-transparent"
                  >
                    View Performance
                  </Button>
                </div>
              </CardContent>
            </ScrollArea>
          </Card>
        </div>
      )}
    </div>
  )
}

/*
BACKEND INTEGRATION GUIDE:
========================

1. MAIN AI ORCHESTRATOR CHATBOT:
   - Connect to: /orchestrator/main.py from your repo
   - API endpoint: POST /api/chat/orchestrator
   - WebSocket: /ws/chat/orchestrator for real-time responses
   - Request format: { message: string, available_agents: string[], context: string }

2. INDIVIDUAL AGENTS:
   - Macro Analyst: /agents/macro_analyst.py
   - Quant Research: /agents/quant_researcher.py  
   - Risk Manager: /agents/risk_manager.py
   - Execution Agent: /agents/execution_agent.py
   
   Each agent needs:
   - Status endpoint: GET /agents/{agent_id}/status
   - Chat endpoint: POST /agents/{agent_id}/chat
   - Details endpoint: GET /agents/{agent_id}/details
   - WebSocket: /ws/agents/{agent_id} for real-time updates

3. REAL-TIME DATA:
   - Agent status updates: WebSocket /ws/agents/status
   - Agent communications: WebSocket /ws/agent-communications
   - Portfolio updates: WebSocket /ws/portfolio

4. REPLACE MOCK DATA:
   - agents state: Connect to your agent status API
   - conversations state: Connect to agent communications API
   - chatMessages: Connect to orchestrator chat history API

5. ENVIRONMENT VARIABLES NEEDED:
   - FASTAPI_BASE_URL: Your backend API base URL
   - WS_BASE_URL: Your WebSocket base URL
   - API_KEY: Authentication key for your backend

6. MODAL INTEGRATION:
   - Connect compute-intensive operations to your Modal functions
   - Backtesting: /modal/backtesting
   - Data processing: /modal/data_processing
   - Strategy optimization: /modal/strategy_optimization
*/
