import { createReducer } from 'redux-act';

import { fetchCollectionStatus } from 'src/actions';
import { objectLoadStart, objectLoadError, objectLoadComplete } from 'src/reducers/util';

const initialState = {};

export default createReducer({
  [fetchCollectionStatus.START]:
    (state, { id }) => objectLoadStart(state, id),

  [fetchCollectionStatus.ERROR]:
    (state, { error, args: { id } }) => objectLoadError(state, id, error),

  [fetchCollectionStatus.COMPLETE]:
    (state, { id, data }) => objectLoadComplete(state, id, data),
}, initialState);
