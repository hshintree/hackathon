"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Brain, FileText, TrendingUp, Globe, AlertCircle, ExternalLink } from "lucide-react"

export default function MarketIntelligence() {
  const [newsItems, setNewsItems] = useState([
    {
      title: "Fed Signals Potential Rate Cuts in Q2",
      source: "Reuters",
      sentiment: "bullish",
      impact: "high",
      timestamp: "15 min ago",
      summary: "Federal Reserve officials hint at possible rate reductions if inflation continues to moderate.",
    },
    {
      title: "Tech Earnings Beat Expectations",
      source: "Bloomberg",
      sentiment: "bullish",
      impact: "medium",
      timestamp: "32 min ago",
      summary: "Major tech companies report stronger than expected Q4 earnings, driving sector optimism.",
    },
    {
      title: "Oil Prices Surge on Supply Concerns",
      source: "CNBC",
      sentiment: "neutral",
      impact: "medium",
      timestamp: "1 hour ago",
      summary: "Crude oil prices jump 3% amid geopolitical tensions affecting supply chains.",
    },
  ])

  const [economicData, setEconomicData] = useState([
    { indicator: "CPI (YoY)", value: "3.2%", change: -0.1, nextRelease: "Jan 15" },
    { indicator: "Unemployment", value: "3.8%", change: 0.0, nextRelease: "Jan 8" },
    { indicator: "GDP Growth", value: "2.4%", change: 0.2, nextRelease: "Jan 25" },
    { indicator: "Fed Funds Rate", value: "5.25%", change: 0.0, nextRelease: "Jan 31" },
  ])

  const [secFilings, setSecFilings] = useState([
    {
      company: "Apple Inc.",
      type: "10-K",
      filed: "2 hours ago",
      keyPoints: ["Strong iPhone sales", "Services revenue growth", "Supply chain optimization"],
    },
    {
      company: "Microsoft Corp.",
      type: "8-K",
      filed: "4 hours ago",
      keyPoints: ["Cloud revenue acceleration", "AI investment expansion", "Dividend increase"],
    },
    {
      company: "Tesla Inc.",
      type: "10-Q",
      filed: "1 day ago",
      keyPoints: ["Production targets met", "Energy business growth", "Autonomous driving progress"],
    },
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      setEconomicData((prev) =>
        prev.map((item) => ({
          ...item,
          value:
            item.indicator === "CPI (YoY)"
              ? `${(Number.parseFloat(item.value) + (Math.random() - 0.5) * 0.1).toFixed(1)}%`
              : item.value,
        })),
      )
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Intelligence Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <Globe className="w-4 h-4" />
              News Sources
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">247</div>
            <div className="text-xs text-emerald-400">Active feeds</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              SEC Filings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">1,247</div>
            <div className="text-xs text-neutral-500">This week</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Market Sentiment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">BULLISH</div>
            <div className="text-xs text-neutral-500">72% positive</div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-neutral-400 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              High Impact Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">3</div>
            <div className="text-xs text-neutral-500">Next 24h</div>
          </CardContent>
        </Card>
      </div>

      {/* Market News */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400 flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Market News & Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {newsItems.map((item, index) => (
              <div key={index} className="p-4 bg-neutral-800 rounded">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h3 className="font-bold text-white mb-1">{item.title}</h3>
                    <p className="text-sm text-neutral-300 mb-2">{item.summary}</p>
                    <div className="flex items-center gap-3 text-xs text-neutral-500">
                      <span>{item.source}</span>
                      <span>{item.timestamp}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 ml-4">
                    <Badge
                      variant={
                        item.sentiment === "bullish"
                          ? "default"
                          : item.sentiment === "bearish"
                            ? "destructive"
                            : "secondary"
                      }
                      className={item.sentiment === "bullish" ? "bg-emerald-500" : ""}
                    >
                      {item.sentiment.toUpperCase()}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={`text-xs ${item.impact === "high" ? "border-red-500 text-red-400" : "border-yellow-500 text-yellow-400"}`}
                    >
                      {item.impact.toUpperCase()} IMPACT
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Economic Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader>
            <CardTitle className="text-emerald-400 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Economic Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {economicData.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-neutral-800 rounded">
                  <div>
                    <div className="font-medium text-white">{item.indicator}</div>
                    <div className="text-sm text-neutral-400">Next: {item.nextRelease}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-white">{item.value}</div>
                    <div className={`text-sm ${item.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {item.change >= 0 ? "+" : ""}
                      {item.change}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-neutral-900 border-neutral-800">
          <CardHeader>
            <CardTitle className="text-emerald-400 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Recent SEC Filings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {secFilings.map((filing, index) => (
                <div key={index} className="p-3 bg-neutral-800 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="font-medium text-white">{filing.company}</div>
                      <div className="text-sm text-neutral-400">
                        Form {filing.type} • {filing.filed}
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="text-neutral-400 hover:text-emerald-400">
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="space-y-1">
                    {filing.keyPoints.map((point, idx) => (
                      <div key={idx} className="text-xs text-neutral-300">
                        • {point}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Analysis */}
      <Card className="bg-neutral-900 border-neutral-800">
        <CardHeader>
          <CardTitle className="text-emerald-400 flex items-center gap-2">
            <Brain className="w-5 h-5" />
            AI Market Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-neutral-800 rounded">
              <h3 className="font-bold text-white mb-2">Sector Rotation Analysis</h3>
              <p className="text-sm text-neutral-300 mb-3">
                AI models detect rotation from growth to value sectors based on recent Fed commentary and economic data
                patterns.
              </p>
              <div className="flex items-center gap-2">
                <Badge className="bg-emerald-500">HIGH CONFIDENCE</Badge>
                <span className="text-xs text-neutral-400">Updated 5 min ago</span>
              </div>
            </div>

            <div className="p-4 bg-neutral-800 rounded">
              <h3 className="font-bold text-white mb-2">Volatility Forecast</h3>
              <p className="text-sm text-neutral-300 mb-3">
                Expected VIX increase to 22-25 range over next 2 weeks based on options flow and historical patterns.
              </p>
              <div className="flex items-center gap-2">
                <Badge variant="secondary">MEDIUM CONFIDENCE</Badge>
                <span className="text-xs text-neutral-400">Updated 12 min ago</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
