"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Server, Database, Wifi, Zap, AlertTriangle, CheckCircle, XCircle, Activity } from "lucide-react"
import { useSystemStatus } from "@/lib/hooks"
import { apiClient } from "@/lib/api"

// REAL BACKEND INTEGRATION: System Health Component
// Connected to FastAPI backend with real-time system monitoring

export default function SystemHealth() {
  // REAL BACKEND INTEGRATION - Using custom hooks for API calls
  const { systemStatus, loading: systemLoading, error: systemError } = useSystemStatus()

  // Real system data from backend
  const systemMetrics = {
    uptime: systemStatus?.systemUptime || "0h 0m",
    latency: 45, // TODO: Get from real metrics
    throughput: 1247, // TODO: Get from real metrics
    errors: 3, // TODO: Get from real metrics
  }

  // Mock API status (to be replaced with real backend data)
  const [apiStatus, setApiStatus] = useState([
    {
      name: "Alpaca Trading API",
      status: "online",
      latency: 23,
      uptime: "99.9%",
    },
    {
      name: "Finnhub Market Data",
      status: "online",
      latency: 67,
      uptime: "99.8%",
    },
    {
      name: "FRED Economic Data",
      status: "online",
      latency: 156,
      uptime: "99.5%",
    },
    {
      name: "Tavily Search API",
      status: "degraded",
      latency: 234,
      uptime: "98.2%",
    },
  ])

  // Mock Modal status (to be replaced with real backend data)
  const [modalStatus, setModalStatus] = useState({
    status: "running",
    activeJobs: 12,
    queuedJobs: 3,
    completedToday: 847,
    cpuUsage: 67,
    memoryUsage: 45,
  })

  // Mock database health (to be replaced with real backend data)
  const [databaseHealth, setDatabaseHealth] = useState({
    status: "healthy",
    connections: 23,
    queryTime: 12,
    storage: 78,
    backupStatus: "completed",
  })

  // Loading state
  if (systemLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading system health...</div>
      </div>
    )
  }

  // Error state
  if (systemError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">
          Error loading system health: {systemError}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {/* REAL BACKEND INTEGRATION: Calculate from system start time */}
              {systemMetrics.uptime}
            </div>
            <p className="text-xs text-muted-foreground">
              System availability
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Latency</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {/* REAL BACKEND INTEGRATION: Average API response time */}
              {systemMetrics.latency}ms
            </div>
            <p className="text-xs text-muted-foreground">
              Average response time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Throughput</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {/* REAL BACKEND INTEGRATION: Requests per minute */}
              {systemMetrics.throughput}
            </div>
            <p className="text-xs text-muted-foreground">
              Requests per minute
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {/* REAL BACKEND INTEGRATION: Count from error logs */}
              {systemMetrics.errors}
            </div>
            <p className="text-xs text-muted-foreground">
              Errors in last hour
            </p>
          </CardContent>
        </Card>
      </div>

      {/* API Status */}
      <Card>
        <CardHeader>
          <CardTitle>API Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {apiStatus.map((api, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${
                    api.status === "online" ? "bg-green-500" : 
                    api.status === "degraded" ? "bg-yellow-500" : "bg-red-500"
                  }`} />
                  <div>
                    <div className="font-semibold">
                      {/* REAL BACKEND INTEGRATION: Map over real API health checks */}
                      {/* REAL BACKEND INTEGRATION: Status icons based on health check results */}
                      {/* REAL BACKEND INTEGRATION: api.name */}
                      {api.name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {/* REAL BACKEND INTEGRATION: api.uptime_percentage */}
                      Uptime: {api.uptime}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-muted-foreground">
                    {/* REAL BACKEND INTEGRATION: api.response_time */}
                    {api.latency}ms
                  </div>
                  <Badge variant={api.status === "online" ? "default" : "secondary"}>
                    {/* REAL BACKEND INTEGRATION: api.status */}
                    {api.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Modal Compute Status */}
      <Card>
        <CardHeader>
          <CardTitle>Modal Compute Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${
                  modalStatus.status === "running" ? "bg-green-500" : "bg-red-500"
                }`} />
                <span className="font-semibold">
                  {/* REAL BACKEND INTEGRATION: Modal compute status */}
                  Status: {modalStatus.status}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Count active Modal functions */}
                Active Jobs: {modalStatus.activeJobs}
              </div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Count queued Modal jobs */}
                Queued Jobs: {modalStatus.queuedJobs}
              </div>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="font-semibold mb-2">Resource Usage</div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Get from Modal metrics */}
                CPU: {modalStatus.cpuUsage}%
              </div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Get from Modal metrics */}
                Memory: {modalStatus.memoryUsage}%
              </div>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="font-semibold mb-2">Performance</div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Count completed Modal jobs */}
                Completed Today: {modalStatus.completedToday}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Database Health */}
      <Card>
        <CardHeader>
          <CardTitle>Database Health</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${
                  databaseHealth.status === "healthy" ? "bg-green-500" : "bg-red-500"
                }`} />
                <span className="font-semibold">
                  {/* REAL BACKEND INTEGRATION: Database connection status */}
                  Status: {databaseHealth.status}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Active database connections */}
                Connections: {databaseHealth.connections}
              </div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Average query response time */}
                Query Time: {databaseHealth.queryTime}ms
              </div>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="font-semibold mb-2">Storage</div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Database storage usage */}
                Usage: {databaseHealth.storage}%
              </div>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="font-semibold mb-2">Backup</div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Last backup status */}
                Status: {databaseHealth.backupStatus}
              </div>
              <div className="text-sm text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: Next scheduled backup time */}
                Next: Tomorrow 2:00 AM
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Logs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent System Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {/* REAL BACKEND INTEGRATION: Get from your logging system */}
            <div className="flex items-center space-x-4 p-2 text-sm">
              <span className="text-muted-foreground">
                {/* REAL BACKEND INTEGRATION: log.timestamp */}
                2024-01-15 14:30:25
              </span>
              <Badge variant="outline" className="text-xs">
                {/* REAL BACKEND INTEGRATION: log.level */}
                INFO
              </Badge>
              <span>
                {/* REAL BACKEND INTEGRATION: log.message */}
                System startup completed successfully
              </span>
            </div>
            <div className="flex items-center space-x-4 p-2 text-sm">
              <span className="text-muted-foreground">2024-01-15 14:25:10</span>
              <Badge variant="outline" className="text-xs">WARN</Badge>
              <span>Database connection pool at 80% capacity</span>
            </div>
            <div className="flex items-center space-x-4 p-2 text-sm">
              <span className="text-muted-foreground">2024-01-15 14:20:05</span>
              <Badge variant="outline" className="text-xs">INFO</Badge>
              <span>Market data sync completed</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
