export function parseExperimentIds(input) {
  if (!input || !input.trim()) return []
  const parts = input.split(',')
  const resultSet = new Set()

  parts.forEach((part) => {
    const trimmed = part.trim()
    if (!trimmed) return

    // Cerca pattern di tipo Range (es. "49-52")
    const rangeMatch = trimmed.match(/^(\d+)\s*-\s*(\d+)$/)
    if (rangeMatch) {
      const start = parseInt(rangeMatch[1], 10)
      const end = parseInt(rangeMatch[2], 10)
      if (!isNaN(start) && !isNaN(end) && start <= end) {
        for (let i = start; i <= end; i++) {
          resultSet.add(String(i))
        }
      } else {
        resultSet.add(trimmed)
      }
    } else {
      resultSet.add(trimmed)
    }
  })

  return Array.from(resultSet)
}