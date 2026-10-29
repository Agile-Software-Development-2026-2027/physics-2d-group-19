const BASE_URL = '/api'

export const getToken = () => sessionStorage.getItem('token')

export async function getHealth() {
  const response = await fetch(`${BASE_URL}/health`)
  if (!response.ok) {
    throw new Error('Health check failed')
  }
  return response.json()
}
