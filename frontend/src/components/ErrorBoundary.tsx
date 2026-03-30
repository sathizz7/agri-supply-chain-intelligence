import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-gray-50">
          <div className="text-center max-w-md p-8">
            <div className="text-5xl mb-4">⚠️</div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h1>
            <p className="text-sm text-gray-500 mb-4">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <p className="text-xs text-gray-400 mb-6">
              Make sure the API server is running: <code className="bg-gray-100 px-1 py-0.5 rounded">uvicorn tfais.api.main:app --reload</code>
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.href = '/'
              }}
              className="bg-[#1B7A3D] text-white px-6 py-2 rounded-lg text-sm hover:bg-[#145c2e] transition"
            >
              Go to Home
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
