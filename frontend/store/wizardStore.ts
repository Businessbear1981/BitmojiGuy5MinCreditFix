import { create } from 'zustand'
import type { DisputeItem } from '@/lib/parseReport'

interface UploadState {
  idUploaded: boolean
  addressUploaded: boolean
  reportUploaded: boolean
  swordUnsheathed: boolean
}

interface FormData {
  firstName: string
  lastName: string
  address: string
  state: string
  bureau: string
  disputeReason: string
}

interface WizardStore {
  currentStep: number
  uploads: UploadState
  formData: FormData
  paid: boolean
  disputeItems: DisputeItem[]
  reportRawText: string
  setStep: (n: number) => void
  setUpload: (key: keyof UploadState, val: boolean) => void
  setFormData: (data: Partial<FormData>) => void
  setPaid: (val: boolean) => void
  setDisputeItems: (items: DisputeItem[]) => void
  setReportRawText: (text: string) => void
}

export const useWizardStore = create<WizardStore>((set) => ({
  currentStep: 1,
  uploads: { idUploaded: false, addressUploaded: false, reportUploaded: false, swordUnsheathed: false },
  formData: { firstName: '', lastName: '', address: '', state: '', bureau: '', disputeReason: '' },
  paid: false,
  disputeItems: [],
  reportRawText: '',
  setStep: (n) => set({ currentStep: n }),
  setUpload: (key, val) => set((s) => ({ uploads: { ...s.uploads, [key]: val } })),
  setFormData: (data) => set((s) => ({ formData: { ...s.formData, ...data } })),
  setPaid: (val) => set({ paid: val }),
  setDisputeItems: (items) => set({ disputeItems: items }),
  setReportRawText: (text) => set({ reportRawText: text }),
}))
