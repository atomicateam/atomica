function transformCascadeData(response) {
  let model = {}

  const cascade = response.cascades
  const stages = response.stages[cascade]
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
  let dataT = []

  results.forEach(r => {
    years = response.t[r]
    dataT = response.data_t
    model[r] = {}

    years.forEach((y, i) => {
      model[r][y] = []

      stages.forEach((stage, stageIndex) => {
        model[r][y].push({
          stage
        })

        pops.forEach(p => {
          const value = response.model[r][cascade][p][stage][i]
          const key = p.replace(/ +/g, '').toLowerCase()

          model[r][y][stageIndex][key] = value
          // console.log(`${r} ${key} ${stage} ${y} ${i} — ${value}`)
        })
      })
    })

    dataT.forEach((y, i) => {
      stages.forEach((stage, stageIndex) => {
        pops.forEach(p => {
          const value = response.data[cascade][p][stage][i]
          const key = p.replace(/ +/g, '').toLowerCase() + '_data'

          model[r][y][stageIndex][key] = value
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
    model
  }

  return dataObj;
}

function transformDataForChartRender(keys, data) {
  const lastIndex = data.length - 1
  const transformed = data.map(d => {
    let obj = { stage: d.stage }
    let total = 0;
    let dataTotal = 0;

    keys.forEach(key => {
      const dataKey = `${key}_data`;

      total += d[key]
      dataTotal += d[dataKey] || 0
      obj[key] = d[key]
      obj[dataKey] = d[dataKey] || 0
    })

    obj._total = total
    obj._dataTotal = dataTotal

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
    const currentData = cascadeData.model[key][year]
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
