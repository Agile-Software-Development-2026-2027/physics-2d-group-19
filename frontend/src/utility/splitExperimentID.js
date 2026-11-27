export function parseExperimentIds(input) {
  if (!input || !input.trim()) return []
  const parts = input.split(',')
  const resultSet = new Set()

  parts.forEach((part) => {
    const trimmed = part.trim()
    if (!trimmed) return

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

export function parseAndValidateExperimentIds(input) {
  const tokens = parseExperimentIds(input)
  const ids = []
  const invalidTokens = []

  for (const token of tokens) {
    if (!/^\d+$/.test(token)) {
      invalidTokens.push(token)
    } else {
      ids.push(Number(token))
    }
  }

  const normalized = input
    .split(',')
    .map((p) => p.trim().replace(/\s*-\s*/, '–'))
    .filter(Boolean)
    .join(', ')

  const summary =
    ids.length > 0 && invalidTokens.length === 0
      ? `${ids.length} experiment${ids.length === 1 ? '' : 's'} will be created: ${normalized}`
      : ''

  return { ids, invalidTokens, summary }
}