/**
 * VRM Bridge Server テストスクリプト
 * Bridge ServerへのWebSocket接続とBlendShape送信をテスト
 */

const WebSocket = require('ws');

console.log('🧪 VRM Bridge Server接続テスト開始...\n');

// WebSocket接続
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  console.log('✅ WebSocket接続成功\n');
  
  // テストメッセージ送信（口を開く）
  console.log('📤 テスト1: 口を開くBlendShape送信（A=0.8）');
  ws.send(JSON.stringify({
    type: 'blend',
    shapes: {
      'A': 0.8,
      'I': 0.0,
      'U': 0.0,
      'E': 0.0,
      'O': 0.0
    }
  }));
  
  // 1秒後に口を閉じる
  setTimeout(() => {
    console.log('📤 テスト2: 口を閉じるBlendShape送信（全て0.0）');
    ws.send(JSON.stringify({
      type: 'blend',
      shapes: {
        'A': 0.0,
        'I': 0.0,
        'U': 0.0,
        'E': 0.0,
        'O': 0.0
      }
    }));
  }, 1000);
  
  // 2秒後に段階的な口の動き
  setTimeout(() => {
    console.log('📤 テスト3: 段階的な口の動き（I→E→A）\n');
    
    let step = 0;
    const interval = setInterval(() => {
      if (step === 0) {
        console.log('  - 小音量: I=0.5');
        ws.send(JSON.stringify({
          type: 'blend',
          shapes: { 'A': 0.0, 'I': 0.5, 'U': 0.0, 'E': 0.0, 'O': 0.0 }
        }));
      } else if (step === 1) {
        console.log('  - 中音量: E=0.7');
        ws.send(JSON.stringify({
          type: 'blend',
          shapes: { 'A': 0.0, 'I': 0.0, 'U': 0.0, 'E': 0.7, 'O': 0.0 }
        }));
      } else if (step === 2) {
        console.log('  - 大音量: A=1.0');
        ws.send(JSON.stringify({
          type: 'blend',
          shapes: { 'A': 1.0, 'I': 0.0, 'U': 0.0, 'E': 0.0, 'O': 0.0 }
        }));
      } else if (step === 3) {
        console.log('  - 口を閉じる: 全て0.0');
        ws.send(JSON.stringify({
          type: 'blend',
          shapes: { 'A': 0.0, 'I': 0.0, 'U': 0.0, 'E': 0.0, 'O': 0.0 }
        }));
        clearInterval(interval);
        
        // テスト完了
        setTimeout(() => {
          console.log('\n✅ テスト完了！');
          console.log('\n📋 期待される動作:');
          console.log('  1. VSeeFaceのVRMモデルの口が開く');
          console.log('  2. 口が閉じる');
          console.log('  3. 口が段階的に開く（I→E→A）');
          console.log('  4. 口が閉じる');
          console.log('\nVSeeFaceで口の動きが確認できましたか？');
          ws.close();
          process.exit(0);
        }, 500);
      }
      step++;
    }, 800);
  }, 2000);
});

ws.on('message', (data) => {
  try {
    const message = JSON.parse(data);
    console.log('📨 Bridge Serverからのメッセージ:', message);
  } catch (err) {
    console.log('📨 Bridge Serverからのメッセージ:', data.toString());
  }
});

ws.on('error', (error) => {
  console.error('❌ WebSocket接続エラー:', error.message);
  console.log('\n💡 確認事項:');
  console.log('  1. Bridge Serverが起動しているか確認してください');
  console.log('     コマンド: npm start');
  console.log('  2. ポート8765が使用可能か確認してください');
  process.exit(1);
});

ws.on('close', () => {
  console.log('\n🔌 WebSocket接続終了');
});
