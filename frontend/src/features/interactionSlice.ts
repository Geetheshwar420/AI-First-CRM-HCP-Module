import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export interface InteractionState {
  hcp_name: string;
  interaction_type: string;
  date: string;
  time: string;
  attendees: string;
  topics_discussed: string;
  materials_shared: string;
  samples_distributed: string;
  sentiment: string;
  outcomes: string;
  follow_up_actions: string;
  suggested_follow_ups: string[];
}

const initialState: InteractionState = {
  hcp_name: '',
  interaction_type: '',
  date: '',
  time: '',
  attendees: '',
  topics_discussed: '',
  materials_shared: '',
  samples_distributed: '',
  sentiment: '',
  outcomes: '',
  follow_up_actions: '',
  suggested_follow_ups: [],
};

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    updateField: (state, action: PayloadAction<{ field: keyof InteractionState; value: any }>) => {
      state[action.payload.field] = action.payload.value;
    },
    updateFromAI: (state, action: PayloadAction<Partial<InteractionState>>) => {
      return { ...state, ...action.payload };
    },
    addFollowUp: (state, action: PayloadAction<string>) => {
      state.follow_up_actions += (state.follow_up_actions ? '\n' : '') + action.payload;
    }
  },
});

export const { updateField, updateFromAI, addFollowUp } = interactionSlice.actions;
export default interactionSlice.reducer;
