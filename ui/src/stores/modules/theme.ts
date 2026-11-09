import { defineStore } from 'pinia'
import { cloneDeep } from 'lodash'
import { useElementPlusTheme } from 'use-element-plus-theme'
import ThemeApi from '@/api/system-settings/theme'
import type {Ref} from "vue";
import BRAND from '@/config/brand'
export interface themeStateTypes {
  themeInfo: any
}
const defalueColor = '#3370FF'
let defaultFaviconHref: string | null = null

const useThemeStore = defineStore('theme', {
  state: (): themeStateTypes => ({
    themeInfo: null,
  }),
  actions: {
    isDefaultTheme() {
      return !this.themeInfo?.theme || this.themeInfo?.theme === defalueColor
    },

    setTheme(data?: any) {
      const { changeTheme } = useElementPlusTheme(this.themeInfo?.theme || defalueColor)
      changeTheme(data?.['theme'] || defalueColor)
      this.themeInfo = cloneDeep(data)
      document.title = data?.title || BRAND.name
      const iconLink = document.querySelector("link[rel~='icon']") as HTMLLinkElement | null
      if (iconLink) {
        if (defaultFaviconHref === null) {
          defaultFaviconHref = iconLink.href
        }
        iconLink.href = data?.icon || defaultFaviconHref
      }
    },

    async theme(loading?: Ref<boolean>) {
      return await ThemeApi.getThemeInfo(loading).then((ok) => {
        this.setTheme(ok.data)
      })
    },
  },
})

export default useThemeStore
