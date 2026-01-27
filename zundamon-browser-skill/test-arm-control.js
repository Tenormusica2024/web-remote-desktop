/**
 * 腕制御機能のテストスクリプト
 * Bridge ServerのWebSocket接続と腕ポーズ制御をテスト
 */

const WebSocket = require('ws');

console.log('🧪 腕制御機能テスト開始...');

// WebSocket接続
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  console.log('✅ Bridge Server接続成功');
  
  // 1秒後に腕を下げる
  setTimeout(() => {
    console.log('📤 腕を下げる指示を送信...');
    ws.send(JSON.stringify({
      type: 'setArmPose',
      isPlaying: true
    }));
  }, 1000);
  
  // 3秒後にT-Poseに戻す
  setTimeout(() => {
    console.log('📤 T-Poseに戻す指示を送信...');
    ws.send(JSON.stringify({
      type: 'setArmPose',
      isPlaying: false
    }));
  }, 3000);
  
  // 5秒後にテスト終了
  setTimeout(() => {
    console.log('✅ テスト完了');
    ws.close();
    process.exit(0);
  }, 5000);
});

ws.on('message', (data) => {
  try {
    const message = JSON.parse(data);
    console.log('📨 Bridge Serverからのメッセージ:', message);
  } catch (err) {
    console.log('📨 Bridge Serverからのメッセージ（raw）:', data.toString());
  }
});

ws.on('error', (error) => {
  console.error('❌ WebSocketエラー:', error.message);
  process.exit(1);
});

ws.on('close', () => {
  console.log('🔌 Bridge Server切断');
});
