// VTubeStudio WebSocket連携モジュール
// VTubeStudioと接続して口パクパラメータをコントロール

class VTubeStudioConnector {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.isAuthenticated = false;
    this.authToken = null;
    this.pluginName = "Zundamon Voice Browser Skill";
    this.pluginDeveloper = "Tenormusica";
    this.port = 8001;
    this.reconnectInterval = null;
    
    // 認証トークンをlocalStorageから読み込み
    this.loadAuthToken();
  }
  
  loadAuthToken() {
    const stored = localStorage.getItem('vts_auth_token');
    if (stored) {
      this.authToken = stored;
      console.log('✅ VTubeStudio認証トークンを読み込み');
    }
  }
  
  saveAuthToken(token) {
    this.authToken = token;
    localStorage.setItem('vts_auth_token', token);
    console.log('✅ VTubeStudio認証トークンを保存');
  }
  
  async connect() {
    if (this.isConnected) {
      console.log('✅ VTubeStudioは既に接続済み');
      return true;
    }
    
    return new Promise((resolve, reject) => {
      try {
        console.log(`🔌 VTubeStudioに接続中... (ws://localhost:${this.port})`);
        this.ws = new WebSocket(`ws://localhost:${this.port}`);
        
        this.ws.onopen = async () => {
          console.log('✅ VTubeStudio WebSocket接続成功');
          this.isConnected = true;
          
          // 認証実行
          const authSuccess = await this.authenticate();
          resolve(authSuccess);
        };
        
        this.ws.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data));
        };
        
        this.ws.onerror = (error) => {
          console.error('❌ VTubeStudio接続エラー:', error);
          this.isConnected = false;
          reject(error);
        };
        
        this.ws.onclose = () => {
          console.log('⚠️ VTubeStudio接続が切断されました');
          this.isConnected = false;
          this.isAuthenticated = false;
          
          // 自動再接続（5秒後）
          if (!this.reconnectInterval) {
            this.reconnectInterval = setTimeout(() => {
              this.reconnectInterval = null;
              this.connect().catch(() => {});
            }, 5000);
          }
        };
        
      } catch (error) {
        console.error('❌ VTubeStudio接続失敗:', error);
        reject(error);
      }
    });
  }
  
  async authenticate() {
    if (this.isAuthenticated) {
      return true;
    }
    
    try {
      // 既存の認証トークンで認証を試行
      if (this.authToken) {
        const authRequest = {
          apiName: "VTubeStudioPublicAPI",
          apiVersion: "1.0",
          requestID: this.generateRequestId(),
          messageType: "AuthenticationRequest",
          data: {
            pluginName: this.pluginName,
            pluginDeveloper: this.pluginDeveloper,
            authenticationToken: this.authToken
          }
        };
        
        const response = await this.sendRequest(authRequest);
        
        if (response.data && response.data.authenticated) {
          console.log('✅ VTubeStudio認証成功（既存トークン）');
          this.isAuthenticated = true;
          return true;
        }
      }
      
      // 新規トークン取得
      const tokenRequest = {
        apiName: "VTubeStudioPublicAPI",
        apiVersion: "1.0",
        requestID: this.generateRequestId(),
        messageType: "AuthenticationTokenRequest",
        data: {
          pluginName: this.pluginName,
          pluginDeveloper: this.pluginDeveloper
        }
      };
      
      const tokenResponse = await this.sendRequest(tokenRequest);
      
      if (tokenResponse.data && tokenResponse.data.authenticationToken) {
        this.saveAuthToken(tokenResponse.data.authenticationToken);
        
        // 新しいトークンで認証
        const authRequest = {
          apiName: "VTubeStudioPublicAPI",
          apiVersion: "1.0",
          requestID: this.generateRequestId(),
          messageType: "AuthenticationRequest",
          data: {
            pluginName: this.pluginName,
            pluginDeveloper: this.pluginDeveloper,
            authenticationToken: this.authToken
          }
        };
        
        const authResponse = await this.sendRequest(authRequest);
        
        if (authResponse.data && authResponse.data.authenticated) {
          console.log('✅ VTubeStudio認証成功（新規トークン）');
          this.isAuthenticated = true;
          return true;
        }
      }
      
      console.error('❌ VTubeStudio認証失敗');
      return false;
      
    } catch (error) {
      console.error('❌ VTubeStudio認証エラー:', error);
      return false;
    }
  }
  
  sendRequest(request) {
    return new Promise((resolve, reject) => {
      if (!this.isConnected || !this.ws) {
        reject(new Error('VTubeStudioに接続されていません'));
        return;
      }
      
      const requestId = request.requestID;
      
      // レスポンス待機
      const messageHandler = (event) => {
        const response = JSON.parse(event.data);
        if (response.requestID === requestId) {
          this.ws.removeEventListener('message', messageHandler);
          resolve(response);
        }
      };
      
      this.ws.addEventListener('message', messageHandler);
      
      // リクエスト送信
      this.ws.send(JSON.stringify(request));
      
      // タイムアウト（10秒）
      setTimeout(() => {
        this.ws.removeEventListener('message', messageHandler);
        reject(new Error('VTubeStudioリクエストタイムアウト'));
      }, 10000);
    });
  }
  
  handleMessage(message) {
    // メッセージハンドリング（イベント通知など）
    console.log('📨 VTubeStudioメッセージ:', message);
  }
  
  async setMouthOpen(value) {
    if (!this.isAuthenticated) {
      console.warn('⚠️ VTubeStudio未認証のため口パクパラメータ送信スキップ');
      return false;
    }
    
    try {
      const request = {
        apiName: "VTubeStudioPublicAPI",
        apiVersion: "1.0",
        requestID: this.generateRequestId(),
        messageType: "InjectParameterDataRequest",
        data: {
          parameterValues: [
            {
              id: "VoiceVolumePlusWhisperVolume",
              value: Math.max(0, Math.min(1, value)) // 0-1の範囲にクランプ
            }
          ]
        }
      };
      
      await this.sendRequest(request);
      return true;
      
    } catch (error) {
      console.error('❌ VTubeStudio口パクパラメータ送信エラー:', error);
      return false;
    }
  }
  
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
  
  disconnect() {
    if (this.reconnectInterval) {
      clearTimeout(this.reconnectInterval);
      this.reconnectInterval = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isAuthenticated = false;
    console.log('🔌 VTubeStudio接続を切断');
  }
}

// グローバルインスタンス
window.vtsConnector = new VTubeStudioConnector();
