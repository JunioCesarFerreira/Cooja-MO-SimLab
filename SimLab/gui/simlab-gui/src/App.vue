<template>
  <n-layout has-sider style="height: 100vh">
    <n-layout-sider width="200" bordered>
      <n-menu
        v-model:value="selected"
        :options="menuOptions"
        @update:value="onSelect"
      />
    </n-layout-sider>

    <n-layout-content class="p-4">
      <component :is="currentComponent" />
    </n-layout-content>
  </n-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NLayout, NLayoutSider, NLayoutContent, NMenu } from 'naive-ui'
import TreeSource from './components/TreeSource.vue'
import TreeExperiment from './components/TreeExperiment.vue'
import TreeQueue from './components/TreeQueue.vue'

const selected = ref('source')

const menuOptions = [
  { label: 'Source', key: 'source' },
  { label: 'Experiment', key: 'experiment' },
  { label: 'Queue', key: 'queue' }
]

const currentComponent = computed(() => {
  switch (selected.value) {
    case 'source': return TreeSource
    case 'experiment': return TreeExperiment
    case 'queue': return TreeQueue
    default: return TreeSource
  }
})

const onSelect = (val) => {
  selected.value = val
}
</script>
