function transformCascadeData(response) {
  let data = {}

  const stageName = response.cascades
  const stages = response.stages[stageName]
  const pops = response.pops
  const results = response.results

  const keys = pops.map(p => {
    const s = p.replace(/ +/g, '')
    return s.toLowerCase()
  })
  let dict = {}
  keys.forEach((k, i) => {
    dict[k] = pops[i]
  })

  let years = []

  results.forEach(r => {
    years = response.t[r]
    data[r] = {}

    years.forEach((y, i) => {
      data[r][y] = []

      stages.forEach((stage, stageIndex) => {
        data[r][y].push({
          stage
        })

        pops.forEach(p => {
          const value = response.model[r][stageName][p][stage][i]
          const key = p.replace(/ +/g, '').toLowerCase()

          data[r][y][stageIndex][key] = value
          // console.log(`${r} ${key} ${stage} ${y} ${i} — ${value}`)
        })
      })
    })            
  })

  const dataObj = {
    keys,
    dict,
    results,
    years,
    data
  }

  return dataObj;
}

function transformDataForChartRender(keys, data) {
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

function getTotal(stage, data) {
  const stageData = data.find(d => d.stage === stage)
  let total = stageData._total
  return total
}

function transformMultiData(keys, cascadeData, year, categories) {
  const scenarios = []
  const multiData = []
  let stages = []

  keys.forEach((key, index) => {
    const currentData = cascadeData.data[key][year]
    scenarios[key] = transformDataForChartRender(categories, currentData)
    if (index === 0) {
      stages = currentData.map(d => d.stage)
    }
  })

  stages.forEach(stage => {
    multiData.push({stage})
    const index = multiData.length - 1
    let highest = 0

    keys.forEach(key => {
      const total = getTotal(stage, scenarios[key])
      
      highest = total > highest ? total : highest

      multiData[index][key] = total
      multiData[index].highest = highest
    })
  })

  return multiData
}

export {
  transformCascadeData,
  transformDataForChartRender,
  transformMultiData
} 
