import test from 'node:test'
import assert from 'node:assert/strict'
import { CROP_GROUPS, TREE_AGE_SUPPORTED_CROPS, VALID_SOIL_TEXTURES } from '../utils/constants.js'

test('CROP_GROUPS contains exactly 22 supported crops in 2 groups', () => {
  assert.equal(CROP_GROUPS.length, 2)

  const hortGroup = CROP_GROUPS.find((g) => g.group.includes('Horticultural'))
  const fieldGroup = CROP_GROUPS.find((g) => g.group.includes('Field'))

  assert.ok(hortGroup, 'Horticultural group must exist')
  assert.ok(fieldGroup, 'Field crops group must exist')

  assert.equal(hortGroup.crops.length, 12, 'Must have exactly 12 horticultural crops')
  assert.equal(fieldGroup.crops.length, 10, 'Must have exactly 10 field crops')

  const totalCrops = hortGroup.crops.length + fieldGroup.crops.length
  assert.equal(totalCrops, 22, 'Must total exactly 22 supported crops')
})

test('Horticultural crops include Mango and other 11 crops', () => {
  const hortGroup = CROP_GROUPS[0]
  const cropNames = hortGroup.crops.map((c) => c.value)

  const expectedHortCrops = [
    'mango', 'banana', 'apple', 'grapes', 'orange',
    'pomegranate', 'papaya', 'coconut', 'coffee',
    'jute', 'watermelon', 'muskmelon',
  ]

  for (const crop of expectedHortCrops) {
    assert.ok(cropNames.includes(crop), `Expected ${crop} to be in horticultural group`)
  }
})

test('Field crops include 10 agronomic crops', () => {
  const fieldGroup = CROP_GROUPS[1]
  const cropNames = fieldGroup.crops.map((c) => c.value)

  const expectedFieldCrops = [
    'rice', 'maize', 'cotton', 'chickpea', 'kidneybeans',
    'pigeonpeas', 'mothbeans', 'mungbean', 'blackgram', 'lentil',
  ]

  for (const crop of expectedFieldCrops) {
    assert.ok(cropNames.includes(crop), `Expected ${crop} to be in field crops group`)
  }
})

test('TREE_AGE_SUPPORTED_CROPS contains the 5 perennial orchard crops', () => {
  assert.equal(TREE_AGE_SUPPORTED_CROPS.length, 5)
  assert.deepEqual(TREE_AGE_SUPPORTED_CROPS.sort(), ['apple', 'coconut', 'mango', 'orange', 'pomegranate'])

  // Verify all 5 have isTree = true in CROP_GROUPS
  const hortCrops = CROP_GROUPS[0].crops
  for (const cropValue of TREE_AGE_SUPPORTED_CROPS) {
    const item = hortCrops.find((c) => c.value === cropValue)
    assert.ok(item, `Crop ${cropValue} must exist in hortCrops`)
    assert.equal(item.isTree, true, `${cropValue} must have isTree: true`)
  }
})

test('Tree age validation boundaries', () => {
  const validateTreeAge = (val) => {
    if (val === '' || val === null || val === undefined) return true
    const n = Number(val)
    if (isNaN(n) || !Number.isInteger(n) || n < 1 || n > 150) {
      return false
    }
    return true
  }

  assert.equal(validateTreeAge('1'), true)
  assert.equal(validateTreeAge('5'), true)
  assert.equal(validateTreeAge('50'), true)
  assert.equal(validateTreeAge('150'), true)

  assert.equal(validateTreeAge('0'), false)
  assert.equal(validateTreeAge('-5'), false)
  assert.equal(validateTreeAge('151'), false)
  assert.equal(validateTreeAge('3.5'), false)
  assert.equal(validateTreeAge('abc'), false)
})
