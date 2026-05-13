'use client'

import { useEffect, useState } from 'react'

export default function TestApiPage() {
  const [message, setMessage] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/hello')

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        setMessage(data.message)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-6 text-gray-800">
          FastAPI Test Page
        </h1>

        <div className="space-y-4">
          {loading && (
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 font-semibold">Error:</p>
              <p className="text-red-500">{error}</p>
            </div>
          )}

          {!loading && !error && message && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <p className="text-green-600 font-semibold mb-2">Success!</p>
              <p className="text-2xl text-gray-800 font-bold text-center">
                {message}
              </p>
              <p className="text-sm text-gray-500 text-center mt-4">
                This message is returned from FastAPI backend
              </p>
            </div>
          )}

          <div className="mt-6 pt-6 border-t border-gray-200">
            <h2 className="font-semibold text-gray-700 mb-2">API Endpoints:</h2>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• <code className="bg-gray-100 px-2 py-1 rounded">/api/hello</code> - FastAPI endpoint</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
