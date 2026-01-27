// VRM ISOLATED/MAIN World Communication Bridge
// このスクリプトはMAIN worldで動作し、ISOLATED worldからのpostMessageを受信してVRMConnectorを制御

(function() {
  'use strict';
  
  // postMessageリスナー設定
  window.addEventListener('message', async (event) => {
    // データ型チェックのみ（ISOLATED worldからのメッセージを受信するためevent.sourceチェックは行わない）
    if (!event.data || typeof event.data !== 'object') return;
    
    const { type, method, params } = event.data;
    
    // VRM関連のメッセージのみ処理
    if (type !== 'VRM_BRIDGE') return;
    
    try {
      switch (method) {
        case 'connect':
          if (window.vrmConnector) {
            const result = await window.vrmConnector.connect();
            window.postMessage({
              type: 'VRM_BRIDGE_RESPONSE',
              method: 'connect',
              success: true,
              result
            }, '*');
          }
          break;
          
        case 'setMouthOpen':
          if (window.vrmConnector && window.vrmConnector.isConnected) {
            await window.vrmConnector.setMouthOpen(params.value);
            // レスポンス不要（高頻度呼び出しのため）
          }
          break;
          
        case 'setArmPose':
          if (window.vrmConnector && window.vrmConnector.isConnected) {
            await window.vrmConnector.setArmPose(params.isPlaying);
            // レスポンス不要
          }
          break;
          
        case 'setEmotion':
          if (window.vrmConnector && window.vrmConnector.isConnected) {
            await window.vrmConnector.setEmotion(params.emotion, params.intensity);
            // レスポンス不要
          }
          break;
          
        case 'setGesture':
          if (window.vrmConnector && window.vrmConnector.isConnected) {
            await window.vrmConnector.setGesture(params.emotion, params.intensity);
            // レスポンス不要
          }
          break;
          
        case 'isConnected':
          window.postMessage({
            type: 'VRM_BRIDGE_RESPONSE',
            method: 'isConnected',
            success: true,
            result: window.vrmConnector?.isConnected || false
          }, '*');
          break;
          
        default:
          console.warn('🌉 VRM Bridge: 未知のメソッド', method);
      }
    } catch (error) {
      // VRM Bridge エラー（静かに失敗）
      window.postMessage({
        type: 'VRM_BRIDGE_RESPONSE',
        method,
        success: false,
        error: error.message
      }, '*');
    }
  });
})();
