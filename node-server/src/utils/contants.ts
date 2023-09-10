const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  ACCEPTED: 202,
  BAD_REQUEST: 400,
  CONFLICT: 409,
  INTERNAL_SERVER_ERROR: 500,
  NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  UNAUTHORIZED: 401,
  PAYMENT_REQUIRED: 402,
  FORBIDDEN: 403,
  TOO_MANY_REQUESTS: 429,
  GATEWAY_TIMEOUT: 504,
};

const API_ROUTES = {
  API_PREFIX: '/api/v1',
  AUTH: '/auth',
  SIGN_UP: 'signUp',
};

export { HTTP_STATUS, API_ROUTES };