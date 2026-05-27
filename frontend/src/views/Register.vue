<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NForm, NFormItem, NInput, NButton, useMessage } from 'naive-ui'
import { authApi } from '@/api/auth'

const router = useRouter()
const message = useMessage()

const form = ref({ email: '', password: '', nickname: '', invitation_code: '' })
const loading = ref(false)

async function onSubmit() {
  if (!form.value.email || !form.value.password || !form.value.invitation_code) {
    message.warning('请填写邮箱、密码和邀请码')
    return
  }
  loading.value = true
  try {
    await authApi.register(form.value)
    message.success('注册成功，请登录')
    router.replace('/login')
  } catch (e) {
    message.error((e as Error).message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <n-card title="注册 · 需要邀请码" style="width: 400px">
      <n-form @submit.prevent="onSubmit">
        <n-form-item label="邮箱">
          <n-input v-model:value="form.email" placeholder="email@example.com" />
        </n-form-item>
        <n-form-item label="昵称（可选）">
          <n-input v-model:value="form.nickname" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input v-model:value="form.password" type="password" show-password-on="click" />
        </n-form-item>
        <n-form-item label="邀请码">
          <n-input v-model:value="form.invitation_code" />
        </n-form-item>
        <n-button type="primary" block :loading="loading" @click="onSubmit">注册</n-button>
        <div style="margin-top: 12px; text-align: center">
          已有账号？<router-link to="/login">返回登录</router-link>
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
