const Apify = require('apify');

Apify.main(async () => {
    // 入力パラメータを取得
    const input = await Apify.getInput();
    console.log('Input:', input);

    const {
        searchKeyword = 'Nintendo Switch',
        maxItems = 20,
        includeImages = true,
        includeDescription = false
    } = input;

    // リクエストキューを作成
    const requestQueue = await Apify.openRequestQueue();
    
    // 検索URLを構築
    const searchUrl = `https://jp.mercari.com/search?keyword=${encodeURIComponent(searchKeyword)}&status=on_sale`;
    
    await requestQueue.addRequest({
        url: searchUrl,
        userData: { label: 'SEARCH' }
    });

    // Puppeteerクローラーを設定
    const crawler = new Apify.PuppeteerCrawler({
        requestQueue,
        launchContext: {
            launchOptions: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            }
        },
        handlePageFunction: async ({ page, request }) => {
            console.log(`Processing ${request.url}...`);
            
            if (request.userData.label === 'SEARCH') {
                // ページが読み込まれるまで待機
                await page.waitForTimeout(3000);
                
                // 商品要素を取得
                const products = await page.evaluate((maxItems, includeImages, includeDescription) => {
                    const items = [];
                    const productElements = document.querySelectorAll('[data-testid="item-cell"]');
                    
                    console.log(`Found ${productElements.length} product elements`);
                    
                    for (let i = 0; i < Math.min(productElements.length, maxItems); i++) {
                        const element = productElements[i];
                        
                        try {
                            // 商品名
                            const titleElement = element.querySelector('span[data-testid="thumbnail-item-name"]');
                            const title = titleElement ? titleElement.textContent.trim() : '';
                            
                            // 価格
                            const priceElement = element.querySelector('span[data-testid="thumbnail-item-price"]');
                            const priceText = priceElement ? priceElement.textContent.trim() : '';
                            const price = priceText.replace(/[¥,]/g, '');
                            
                            // 商品URL
                            const linkElement = element.querySelector('a');
                            const url = linkElement ? 'https://jp.mercari.com' + linkElement.getAttribute('href') : '';
                            
                            // 画像URL
                            let imageUrl = '';
                            if (includeImages) {
                                const imgElement = element.querySelector('img');
                                imageUrl = imgElement ? imgElement.src : '';
                            }
                            
                            // 商品状態
                            const conditionElement = element.querySelector('[data-testid="thumbnail-item-condition"]');
                            const condition = conditionElement ? conditionElement.textContent.trim() : '';
                            
                            if (title && price) {
                                const item = {
                                    title: title,
                                    price: parseInt(price) || 0,
                                    priceText: priceText,
                                    url: url,
                                    condition: condition,
                                    platform: 'mercari',
                                    currency: 'JPY'
                                };
                                
                                if (includeImages && imageUrl) {
                                    item.imageUrl = imageUrl;
                                }
                                
                                items.push(item);
                            }
                        } catch (error) {
                            console.log('Error processing item:', error);
                        }
                    }
                    
                    return items;
                }, maxItems, includeImages, includeDescription);
                
                console.log(`Scraped ${products.length} products`);
                
                // 結果をデータセットに保存
                await Apify.pushData(products);
            }
        },
        handleFailedRequestFunction: async ({ request }) => {
            console.log(`Request ${request.url} failed too many times`);
        },
        maxRequestRetries: 3,
        requestTimeoutSecs: 60
    });

    // クローラーを実行
    await crawler.run();
    
    console.log('Crawler finished.');
});
