<template>
  <img v-if="theme.themeInfo?.loginLogo" :src="fileURL" alt="" height="45px" class="mr-8" />
  <div v-else class="brand-logo" :style="{ height }">
    <img class="brand-logo-icon" :style="{ height: iconHeight }" :src="brandIcon" alt="" />
    <span class="brand-logo-text" :style="{ fontSize, lineHeight: height }">{{ BRAND.name }}</span>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import useStore from '@/stores'
import BRAND from '@/config/brand'
import defaultLogo from '@/assets/logo/logo.png'

defineOptions({ name: 'LogoFull' })

const props = defineProps({
  height: {
    type: String,
    default: '36px',
  },
})

const { theme } = useStore()

const fontSize = computed(() => `calc(${props.height} * 0.5)`)
const iconHeight = computed(() => `calc(${props.height} * 0.8)`)

const brandIcon = computed(() => {
  const icon = theme.themeInfo?.icon
  if (!icon) {
    return defaultLogo
  }
  return typeof icon === 'string' ? icon : URL.createObjectURL(icon)
})

const fileURL = computed(() => {
  if (theme.themeInfo) {
    if (typeof theme.themeInfo?.loginLogo === 'string') {
      return theme.themeInfo?.loginLogo
    } else {
      return URL.createObjectURL(theme.themeInfo?.loginLogo)
    }
  } else {
    return ''
  }
})
</script>
<style lang="scss" scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.brand-logo-icon {
  width: auto;
  object-fit: contain;
  flex-shrink: 0;
}

.brand-logo-text {
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  letter-spacing: 0.02em;
}
</style>
