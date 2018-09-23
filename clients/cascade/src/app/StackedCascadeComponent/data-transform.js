export default function(keys, data) {
  const lastIndex = data.length - 1
  const transformed = data.map(d => {
    let obj = { stage: d.stage }
    let total = 0;

    keys.forEach(key => {
      total += d[key]
      obj[key] = d[key]
    })

    obj._total = total

    return obj
  })

  transformed.forEach((d, i) => {
    if (i === lastIndex) {
      d.loss = 0
      d.conversion = 0
    } else {
      d.loss = transformed[i]._total - transformed[i+1]._total
      d.conversion = transformed[i+1]._total / transformed[i]._total * 100
    }
  })

  return transformed
}
