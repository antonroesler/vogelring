exports.handler = async (event) => {
    const request = event.Records[0].cf.request;
  
    if (request.headers.authorization === undefined) {
      return UnauthorizedResponse;
    }
  
    const authorizationToken = request.headers.authorization[0].value;
  
    const credentials = decodeAuthToken(authorizationToken);
    if (credentials === null) {
      return UnauthorizedResponse;
    }
  
    const config = this.loadConfiguration();
  
    const username = credentials.username;
    const passwordHash = hashedPassword(credentials.password, config.password_salt);
  
    if (username !== config.username || passwordHash !== config.password_hash) {
      return UnauthorizedResponse;
    }
  
    return request;
  };