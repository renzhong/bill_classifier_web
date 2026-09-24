<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NDialogProvider, NLoadingBarProvider, zhCN, dateZhCN } from 'naive-ui'

const themeOverrides = {
  common: { primaryColor: '#a6c8ff', primaryColorHover: '#d0e2ff', primaryColorPressed: '#a6c8ff',
    primaryColorSuppl: '#d0e2ff', bodyColor: '#f4f4f4', cardColor: '#ffffff', textColorBase: '#161616' },
  Button: { textColorPrimary: '#161616', textColorHoverPrimary: '#161616', textColorFocusPrimary: '#161616',
    textColorPressedPrimary: '#161616' },
}
</script>

<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN" :theme-overrides="themeOverrides">
    <n-loading-bar-provider>
      <n-dialog-provider>
        <n-message-provider>
          <router-view />
        </n-message-provider>
      </n-dialog-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>
