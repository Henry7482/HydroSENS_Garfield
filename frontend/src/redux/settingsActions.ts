// Action Types
export const SET_SELECTED_METRICS = "SET_SELECTED_METRICS"
export const SET_ENDMEMBER_TYPE = "SET_ENDMEMBER_TYPE"
export const TOGGLE_SETTINGS_MODAL = "TOGGLE_SETTINGS_MODAL"
export const RESET_SETTINGS = "RESET_SETTINGS"

// Available metrics
export const AVAILABLE_METRICS = [
  { key: "ndvi", label: "Normalized Difference Vegetation Index (NDVI)" },
  { key: "vegetation-fraction", label: "Vegetation Fraction" },
  { key: "soil-fraction", label: "Soil Fraction" },
  { key: "precipitation", label: "Precipitation" },
  { key: "temperature", label: "Temperature" },
  { key: "curve-number", label: "Curve Number" },
] as const

// Endmember types
export const ENDMEMBER_TYPES = [
  { value: "2", label: "Agricultural" },
  { value: "3", label: "Urban" },
] as const

export type MetricKey = (typeof AVAILABLE_METRICS)[number]["key"]
export type EndmemberType = (typeof ENDMEMBER_TYPES)[number]["value"]

// Action Creators
export const setSelectedMetrics = (metrics: MetricKey[]) => ({
  type: SET_SELECTED_METRICS,
  payload: metrics,
})

export const setEndmemberType = (endmemberType: EndmemberType) => ({
  type: SET_ENDMEMBER_TYPE,
  payload: endmemberType,
})

export const toggleSettingsModal = (isOpen: boolean) => ({
  type: TOGGLE_SETTINGS_MODAL,
  payload: isOpen,
})

export const resetSettings = () => ({
  type: RESET_SETTINGS,
})

// Action Types Definition
export interface SetSelectedMetricsAction {
  type: typeof SET_SELECTED_METRICS
  payload: MetricKey[]
}

export interface SetEndmemberTypeAction {
  type: typeof SET_ENDMEMBER_TYPE
  payload: EndmemberType
}

export interface ToggleSettingsModalAction {
  type: typeof TOGGLE_SETTINGS_MODAL
  payload: boolean
}

export interface ResetSettingsAction {
  type: typeof RESET_SETTINGS
}

export type SettingsActionTypes =
  | SetSelectedMetricsAction
  | SetEndmemberTypeAction
  | ToggleSettingsModalAction
  | ResetSettingsAction
