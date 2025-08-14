const API_BASE_URL = typeof window !== 'undefined' ? 'http://localhost:8080' : 'http://localhost:8080'

export interface AgentChatRequest {
  query: string
}

export interface AgentChatResponse {
  state: {
    query: string
    intent: string
    context?: any[]
    plan?: string
    result?: any
    error?: string
  }
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async chat(request: AgentChatRequest): Promise<AgentChatResponse> {
    const response = await fetch(`${this.baseUrl}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`)
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`)
    }
    return response.json()
  }
}

export const apiClient = new ApiClient()
