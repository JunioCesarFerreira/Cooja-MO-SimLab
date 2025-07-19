<template>
  <n-card title="Source Files Tree">
    <n-tree
      :data="treeData"
      default-expand-all
      :render-label="renderLabel"
    />
  </n-card>
</template>

<script setup>
import { ref } from 'vue'
import { NTree, NCard } from 'naive-ui'

const treeData = ref([
  {
    label: 'Dataset A',
    key: 'dataset-a',
    children: [
      {
        label: 'simulation.xml',
        key: 'sim-xml'
      },
      {
        label: 'positions.dat',
        key: 'pos-dat'
      }
    ]
  },
  {
    label: 'Dataset B',
    key: 'dataset-b',
    children: [
      {
        label: 'main.csc',
        key: 'main-csc'
      }
    ]
  }
])

const renderLabel = ({ option }) => option.label
</script>
