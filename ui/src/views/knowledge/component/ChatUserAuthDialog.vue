<template>
  <el-dialog
    v-model="visible"
    :title="$t('views.knowledge.setting.chatUserAuth')"
    width="560px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <el-alert
      :title="$t('views.knowledge.setting.chatUserAuthTip')"
      type="info"
      :closable="false"
      class="mb-16"
    />
    <el-form label-position="top" v-loading="loading">
      <el-form-item :label="$t('views.knowledge.setting.chatUserAuthUser')">
        <el-select
          v-model="userIds"
          multiple
          filterable
          class="w-full"
          :placeholder="$t('common.selectPlaceholder')"
        >
          <el-option
            v-for="item in userOptions"
            :key="item.id"
            :label="item.nick_name ? `${item.nick_name}（${item.username}）` : item.username"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('views.knowledge.setting.chatUserAuthGroup')">
        <el-select
          v-model="groupIds"
          multiple
          filterable
          class="w-full"
          :placeholder="$t('common.selectPlaceholder')"
        >
          <el-option v-for="item in groupOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">{{ $t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="loading" @click="save">
        {{ $t('common.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { t } from '@/locales'
import { MsgSuccess } from '@/utils/message'
import { loadPermissionApi } from '@/utils/dynamics-api/permission-api'
import KnowledgeChatUserAuthApi from '@/api/system/knowledge-chat-user-auth'

const visible = ref(false)
const loading = ref(false)
const knowledgeId = ref('')
const userIds = ref<string[]>([])
const groupIds = ref<string[]>([])
const userOptions = ref<any[]>([])
const groupOptions = ref<any[]>([])

async function open(item: any) {
  knowledgeId.value = item.id
  userIds.value = []
  groupIds.value = []
  userOptions.value = []
  groupOptions.value = []
  visible.value = true
  loading.value = true
  try {
    const [authRes, userRes, groupRes] = await Promise.all([
      KnowledgeChatUserAuthApi.getAuth(item.id),
      loadPermissionApi('chatUser').getChatUserList(),
      loadPermissionApi('userGroup').getUserGroup(),
    ])
    userIds.value = authRes?.data?.user_ids || []
    groupIds.value = authRes?.data?.group_ids || []
    userOptions.value = userRes?.data || []
    groupOptions.value = groupRes?.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function save() {
  loading.value = true
  KnowledgeChatUserAuthApi.putAuth(knowledgeId.value, {
    user_ids: userIds.value,
    group_ids: groupIds.value,
  })
    .then(() => {
      MsgSuccess(t('common.saveSuccess'))
      visible.value = false
    })
    .finally(() => {
      loading.value = false
    })
}

defineExpose({ open })
</script>
<style scoped lang="scss"></style>
