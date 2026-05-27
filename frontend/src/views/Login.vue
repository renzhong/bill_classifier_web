<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { authApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const user = useUserStore()

const form = ref({ email: '', password: '' })
const loading = ref(false)

async function onSubmit() {
  if (!form.value.email || !form.value.password) {
    message.warning('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    const tokens = await authApi.login(form.value)
    user.setTokens(tokens.access_token, tokens.refresh_token)
    await user.fetchMe()
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <n-card title="登录 · Bill Classifier" style="width: 380px">
      <n-form @submit.prevent="onSubmit">
        <n-form-item label="邮箱">
          <n-input v-model:value="form.email" placeholder="email@example.com" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="onSubmit">登录</n-button>
        <div style="margin-top: 12px; text-align: center">
          还没有账号？<router-link to="/register">用邀请码注册</router-link>
        </div>
      </n-form>
    </n-card>
  </div>
</template>

<style scoped>
.auth-wrap {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
