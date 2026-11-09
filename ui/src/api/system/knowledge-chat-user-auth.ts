import { Result } from '@/request/Result'
import { get, put } from '@/request/index'
import type { Ref } from 'vue'

const prefix = '/system/chat_user/authorize/knowledge'

/**
 * 获取知识库的对话用户/用户组授权
 */
const getAuth: (knowledge_id: string, loading?: Ref<boolean>) => Promise<Result<any>> = (
  knowledge_id,
  loading,
) => {
  return get(`${prefix}/${knowledge_id}`, undefined, loading)
}

/**
 * 保存知识库的对话用户/用户组授权
 * data: { user_ids: string[], group_ids: string[] }
 */
const putAuth: (knowledge_id: string, data: any, loading?: Ref<boolean>) => Promise<Result<any>> = (
  knowledge_id,
  data,
  loading,
) => {
  return put(`${prefix}/${knowledge_id}`, data, {}, loading)
}

export default {
  getAuth,
  putAuth,
}
