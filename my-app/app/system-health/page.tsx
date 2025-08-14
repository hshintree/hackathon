"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Server, Database, Wifi, Zap, AlertTriangle, CheckCircle, XCircle, Activity } from "lucide-react"

export default function SystemHealth() {
  const [systemMetrics, setSystemMetrics] = useState({
    uptime: "99.97%",
    latency: 45,
    throughput: 1247,
    errors: 3,
  })

  const [apiStatus, setApiStatus] = useState([
    { name: "Alpaca Trading API", status: "online", latency: 23, uptime: "99.9%" },
    { name: "Finnhub Market Data", status: "online", latency: 67, uptime: "99.8%" },
    { name: "FRED Economic Data", status: "online", latency: 156, uptime: "99.5%" },
    { name: "Tavily Search API", status: "degraded", latency: 234, uptime: "98.2%" },
  ])

  const [modalStatus, setModalStatus] = useState({
    status: "running",
    activeJobs: 12,
    queuedJobs: 3,
    completedToday: 847,
    cpuUsage: 67,
    memoryUsage: 45,
  })

  const [databaseHealth, setDatabaseHealth] = useState({
    status: "healthy",
    connections: 23,
    queryTime: 12,
    storage: 78,
    backupStatus: "completed",
  })

  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics((prev) => ({
        ...prev,
        latency: Math.max(20, Math.min(100, prev.latency + (Math.random() - 0.5) * 10)),
        throughput: Math.max(800, Math.min(2000, prev.throughput + (Math.random() - 0.5) * 100)),
      }))

      setModalStatus((prev) => ({
        ...prev,
        activeJobs: Math.max(5, Math.min(20, prev.activeJobs + Math.floor((Math.random() - 0.5) * 4))),
        cpuUsage: Math.max(30, Math.min(90, prev.cpuUsage + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.max(20, Math.min(80, prev.memoryUsage + (Math.random() - 0.5) * 8)),
      }))
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 space-y-6">
      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              System Uptime
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">{systemMetrics.uptime}</div>
            <div className="text-xs text-neutral-500">Last 30 days</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Avg Latency
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{systemMetrics.latency}ms</div>
            <div className="text-xs text-emerald-400">Within SLA</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <Server className="w-4 h-4" />
              Throughput
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{systemMetrics.throughput}</div>
            <div className="text-xs text-neutral-500">req/min</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Active Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">{systemMetrics.errors}</div>
            <div className="text-xs text-neutral-500">Low priority</div>
          </CardContent>
        </Card>
      </div>

      {/* API Status */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400 flex items-center gap-2">
            <Wifi className="w-5 h-5" />
            API Connections
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {apiStatus.map((api, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-neutral-800 rounded">
                <div className="flex items-center gap-3">
                  {api.status === "online" ? (
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                  ) : api.status === "degraded" ? (
                    <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400" />
                  )}
                  <div>
                    <div className="font-medium text-white">{api.name}</div>
                    <div className="text-sm text-neutral-400">Uptime: {api.uptime}</div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm text-neutral-400">Latency</div>
                    <div className="font-bold text-white">{api.latency}ms</div>
                  </div>
                  <Badge
                    variant={
                      api.status === "online" ? "default" : api.status === "degraded" ? "secondary" : "destructive"
                    }
                    className={api.status === "online" ? "bg-emerald-500" : ""}
                  >
                    {api.status.toUpperCase()}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Modal Compute Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader>
            <CardTitle className="text-emerald-400 flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Modal Compute
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-neutral-400">Status</span>
                <Badge className="bg-emerald-500">RUNNING</Badge>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-neutral-400">Active Jobs</div>
                  <div className="text-xl font-bold text-white">{modalStatus.activeJobs}</div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">Queued Jobs</div>
                  <div className="text-xl font-bold text-white">{modalStatus.queuedJobs}</div>
                </div>
              </div>

              <div>
                <div className="text-sm text-neutral-400 mb-2">CPU Usage</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-neutral-700 rounded-full h-2">
                    <div
                      className="bg-emerald-400 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${modalStatus.cpuUsage}%` }}
                    />
                  </div>
                  <span className="text-sm text-white">{modalStatus.cpuUsage}%</span>
                </div>
              </div>

              <div>
                <div className="text-sm text-neutral-400 mb-2">Memory Usage</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-neutral-700 rounded-full h-2">
                    <div
                      className="bg-blue-400 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${modalStatus.memoryUsage}%` }}
                    />
                  </div>
                  <span className="text-sm text-white">{modalStatus.memoryUsage}%</span>
                </div>
              </div>

              <div className="text-sm text-neutral-500">Completed today: {modalStatus.completedToday} jobs</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader>
            <CardTitle className="text-emerald-400 flex items-center gap-2">
              <Database className="w-5 h-5" />
              Database Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-neutral-400">Status</span>
                <Badge className="bg-emerald-500">HEALTHY</Badge>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-neutral-400">Connections</div>
                  <div className="text-xl font-bold text-white">{databaseHealth.connections}</div>
                </div>
                <div>
                  <div className="text-sm text-neutral-400">Avg Query Time</div>
                  <div className="text-xl font-bold text-white">{databaseHealth.queryTime}ms</div>
                </div>
              </div>

              <div>
                <div className="text-sm text-neutral-400 mb-2">Storage Usage</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-neutral-700 rounded-full h-2">
                    <div className="bg-purple-400 h-2 rounded-full" style={{ width: `${databaseHealth.storage}%` }} />
                  </div>
                  <span className="text-sm text-white">{databaseHealth.storage}%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-neutral-400">Last Backup</span>
                <Badge variant="outline" className="border-emerald-500 text-emerald-400">
                  COMPLETED
                </Badge>
              </div>

              <div className="text-sm text-neutral-500">Next backup: Tonight at 2:00 AM UTC</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Logs */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400">Recent System Events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 font-mono text-sm">
            {[
              { time: "14:23:45", level: "INFO", message: "Modal job completed: backtest_momentum_strategy" },
              { time: "14:22:12", level: "WARN", message: "Tavily API response time elevated: 234ms" },
              { time: "14:20:33", level: "INFO", message: "Database backup initiated" },
              { time: "14:18:07", level: "INFO", message: "New trading signal generated: AAPL BUY" },
              { time: "14:15:44", level: "ERROR", message: "Failed to connect to secondary data feed" },
            ].map((log, index) => (
              <div key={index} className="flex items-center gap-4 p-2 bg-neutral-800 rounded text-xs">
                <span className="text-neutral-500">{log.time}</span>
                <Badge
                  variant={log.level === "ERROR" ? "destructive" : log.level === "WARN" ? "secondary" : "default"}
                  className={`text-xs ${log.level === "INFO" ? "bg-emerald-500" : ""}`}
                >
                  {log.level}
                </Badge>
                <span className="text-neutral-300">{log.message}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
