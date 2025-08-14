"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Bot, Brain, Shield, Target, TrendingUp, Activity, MessageSquare, Settings, Send, User } from "lucide-react"
import { useAgentStatus, useAgentChat } from "@/lib/hooks"
import { apiClient } from "@/lib/api"

// REAL BACKEND INTEGRATION: Agent Network Component
// Connected to FastAPI backend with real-time agent status and chat functionality

export default function AgentNetwork() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [chatInput, setChatInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)

  // REAL BACKEND INTEGRATION - Using custom hooks for API calls
  const { agentStatus, loading: agentLoading, error: agentError } = useAgentStatus()
  const { chatMessages, sendMessage, loading: chatLoading } = useAgentChat()

  // Real agent data from backend
  const agents = agentStatus?.agents || []

  // Agent icons mapping
  const agentIcons = {
    "macro-analyst": Brain,
    "quant-research": TrendingUp,
    "risk-manager": Shield,
    "execution-agent": Target,
  }

  // Agent colors mapping
  const agentColors = {
    "macro-analyst": "blue",
    "quant-research": "emerald", 
    "risk-manager": "red",
    "execution-agent": "purple",
  }

  // Loading state
  if (agentLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading agent network...</div>
      </div>
    )
  }

  // Error state
  if (agentError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">
          Error loading agent network: {agentError}
        </div>
      </div>
    )
  }

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return

    setIsTyping(true)
    try {
      await sendMessage(chatInput)
      setChatInput("")
    } catch (error) {
      console.error("Failed to send message:", error)
    } finally {
      setIsTyping(false)
    }
  }

  const handleAgentSelect = (agentId: string) => {
    setSelectedAgent(agentId)
  }

  return (
    <div className="space-y-6">
      {/* Agent Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {agents.map((agent) => {
          const IconComponent = agentIcons[agent.id as keyof typeof agentIcons] || Bot
          const color = agentColors[agent.id as keyof typeof agentColors] || "gray"
          
          return (
            <Card key={agent.id} className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => handleAgentSelect(agent.id)}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <IconComponent className={`w-5 h-5 text-${color}-500`} />
                    <CardTitle className="text-sm">{agent.name}</CardTitle>
                  </div>
                  <Badge variant={agent.status === "active" ? "default" : "secondary"}>
                    {agent.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">
                    Last Activity: {agent.lastActivity}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    ID: {agent.id}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Agent Chat Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Messages */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Agent Communications
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-4">
                  {chatMessages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.role === "user"
                            ? "bg-blue-500 text-white"
                            : "bg-gray-100 text-gray-900"
                        }`}
                      >
                        <div className="text-sm">{message.content}</div>
                        <div className="text-xs opacity-70 mt-1">
                          {message.timestamp}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
                        <div className="text-sm">Agent is typing...</div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              
              {/* Chat Input */}
              <div className="flex gap-2 mt-4">
                <Input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask the agents anything..."
                  onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                  disabled={chatLoading}
                />
                <Button onClick={handleSendMessage} disabled={chatLoading || !chatInput.trim()}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Agent Details */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Agent Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedAgent ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold">Selected Agent</h3>
                    <p className="text-sm text-muted-foreground">
                      {agents.find(a => a.id === selectedAgent)?.name || selectedAgent}
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold">Status</h3>
                    <p className="text-sm text-muted-foreground">
                      {agents.find(a => a.id === selectedAgent)?.status || "Unknown"}
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold">Last Activity</h3>
                    <p className="text-sm text-muted-foreground">
                      {agents.find(a => a.id === selectedAgent)?.lastActivity || "Unknown"}
                    </p>
                  </div>
                  
                  <Button 
                    className="w-full"
                    onClick={() => {
                      // REAL BACKEND INTEGRATION: Start direct conversation with specific agent
                      setChatInput(`/agent ${selectedAgent} Hello, can you provide a status update?`)
                    }}
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Chat with Agent
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => {
                      // REAL BACKEND INTEGRATION: Open agent configuration
                      console.log("Open configuration for agent:", selectedAgent)
                    }}
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    Configure Agent
                  </Button>
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  Select an agent to view details
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Decisions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Recent Agent Decisions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* REAL BACKEND INTEGRATION: Connect to your main AI orchestrator from /orchestrator/main.py */}
            {/* REAL BACKEND INTEGRATION: /agents/{agent.id}/decisions endpoint */}
            <div className="text-center text-muted-foreground py-8">
              Agent decision history will be displayed here
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
