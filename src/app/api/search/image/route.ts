import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import { v4 as uuidv4 } from 'uuid';

// 画像検索APIエンドポイント
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const imageFile = formData.get('image') as File;
    
    if (!imageFile) {
      return NextResponse.json(
        { error: 'No image file provided' },
        { status: 400 }
      );
    }

    // 画像を一時的に保存
    const tempDir = path.join(process.cwd(), 'tmp');
    await fs.mkdir(tempDir, { recursive: true });
    
    const fileName = `${uuidv4()}-${imageFile.name}`;
    const filePath = path.join(tempDir, fileName);
    
    const arrayBuffer = await imageFile.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    await fs.writeFile(filePath, buffer);

    try {
      // Python画像処理スクリプトを実行
      const pythonScript = path.join(process.cwd(), 'scripts', 'process_image_search.py');
      
      const result = await new Promise<any>((resolve, reject) => {
        const pythonProcess = spawn('python3', [pythonScript, filePath], {
          env: { ...process.env },
          timeout: 30000 // 30秒のタイムアウト
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        pythonProcess.on('close', (code) => {
          if (code !== 0) {
            reject(new Error(`Python process exited with code ${code}: ${stderr}`));
          } else {
            try {
              const result = JSON.parse(stdout);
              resolve(result);
            } catch (e) {
              reject(new Error(`Failed to parse Python output: ${stdout}`));
            }
          }
        });

        pythonProcess.on('error', (error) => {
          reject(error);
        });
      });

      // 一時ファイルを削除
      await fs.unlink(filePath);

      // 抽出された情報から検索を実行
      if (result.jan_codes && result.jan_codes.length > 0) {
        // JANコードが見つかった場合は既存のJAN検索を使用
        const searchUrl = new URL('/api/search/all', request.url);
        searchUrl.searchParams.set('q', result.jan_codes[0]);
        searchUrl.searchParams.set('platforms', 'ebay,mercari,yahoo');
        
        const searchResponse = await fetch(searchUrl.toString());
        const searchData = await searchResponse.json();
        
        return NextResponse.json({
          extraction_result: result,
          search_results: searchData,
          search_type: 'jan_code'
        });
        
      } else if (result.product_name) {
        // 商品名が見つかった場合は商品名検索を使用
        // TODO: 商品名検索エンドポイントが実装されたら使用
        return NextResponse.json({
          extraction_result: result,
          search_results: null,
          search_type: 'product_name',
          message: 'Product name search will be available soon'
        });
        
      } else {
        // 情報が抽出できなかった場合
        return NextResponse.json({
          extraction_result: result,
          search_results: null,
          search_type: 'none',
          message: 'No product information could be extracted from the image'
        });
      }

    } catch (error) {
      // エラーが発生してもファイルを削除
      try {
        await fs.unlink(filePath);
      } catch (e) {
        // ファイル削除エラーは無視
      }
      throw error;
    }

  } catch (error) {
    console.error('Image search error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Image search failed' },
      { status: 500 }
    );
  }
}

// オプション：画像URLからの検索
export async function PUT(request: NextRequest) {
  try {
    const { imageUrl } = await request.json();
    
    if (!imageUrl) {
      return NextResponse.json(
        { error: 'No image URL provided' },
        { status: 400 }
      );
    }

    // URLから画像をダウンロード
    const response = await fetch(imageUrl);
    const arrayBuffer = await response.arrayBuffer();
    
    // 一時ファイルとして保存
    const tempDir = path.join(process.cwd(), 'tmp');
    await fs.mkdir(tempDir, { recursive: true });
    
    const fileName = `${uuidv4()}.jpg`;
    const filePath = path.join(tempDir, fileName);
    
    const buffer = Buffer.from(arrayBuffer);
    await fs.writeFile(filePath, buffer);

    // 同じ処理を実行
    const pythonScript = path.join(process.cwd(), 'scripts', 'process_image_search.py');
    
    const result = await new Promise<any>((resolve, reject) => {
      const pythonProcess = spawn('python3', [pythonScript, filePath], {
        env: { ...process.env },
        timeout: 30000
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', async (code) => {
        // ファイルを削除
        try {
          await fs.unlink(filePath);
        } catch (e) {
          // エラーは無視
        }

        if (code !== 0) {
          reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        } else {
          try {
            const result = JSON.parse(stdout);
            resolve(result);
          } catch (e) {
            reject(new Error(`Failed to parse Python output: ${stdout}`));
          }
        }
      });
    });

    // 結果に基づいて検索
    if (result.jan_codes && result.jan_codes.length > 0) {
      const searchUrl = new URL('/api/search/all', request.url);
      searchUrl.searchParams.set('q', result.jan_codes[0]);
      searchUrl.searchParams.set('platforms', 'ebay,mercari,yahoo');
      
      const searchResponse = await fetch(searchUrl.toString());
      const searchData = await searchResponse.json();
      
      return NextResponse.json({
        extraction_result: result,
        search_results: searchData,
        search_type: 'jan_code'
      });
    } else {
      return NextResponse.json({
        extraction_result: result,
        search_results: null,
        search_type: result.product_name ? 'product_name' : 'none'
      });
    }

  } catch (error) {
    console.error('Image URL search error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Image URL search failed' },
      { status: 500 }
    );
  }
}