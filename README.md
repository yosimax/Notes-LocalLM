# Notes-LocalLM (small language model)

## macbook air M4 24GB でエージェントコーディング copenode+llama.cpp (小規模 Local LM)

OepnCode と llama.cpp (llama-server)で、AI Agent環境をどの程度使えるのか、これまでもblogに書いてきたがメモ書き程度ならいいけど、凝った表現がHTMLで書かないといけないので、Githubに書き残していこうかと思う。

- これまでの構築の流れを思い出して書いてみる （だいぶ省略しているけどおおよその流れはこんな感じ）。
1. macbook air M4 24GBを購入して、初のLLM使用
   ollamaをインストールして、webuiをdockerで起動していくつかのモデルを呼び出してそれなりのレスポンス速度で返ってくることを確認。

1. vscode & Github copilotからollamaのモデルを使ってみる
   vscode、Github copilotからollamaのモデルを呼び出すことを試行錯誤するが、どうにもollama (/ webui)を直に呼ぶよりも圧倒的に遅い（緩慢）、使用するコンテキストサイズが大きく、どうにもこうにも使い物にならない。

   例：
  
   ```
   「こんにちは」の入力に対して、ollamaが呼ばれるまでのオーバーヘッドの時間がある。
   →Github copilot （ハーネス）部分の処理があるので、やむなし。
   スクリプトのリファクタリングをやらせてみると、コンテキストサイズが256K,128Kなどのモデルを使用していたためなのか（メモリが不足していて？）処理が進まなくなってしまう。
   ```

1. vscode & Github copilotではなく、Cluade Codeからollamaを呼んだらどうなるか
   Cluade Codeからollamaのいくつかのモデルを呼び出してみたが、今一つ使い方がわかっていないというか、メモリサイズに合わせたollama側のチューニングなどが原因なのか、うまく動かせるようになるように思えない。

1. Claude codeやvscode & Github copilotから軽そうなopencodeに変えてみる
   vscodeもメモリを大きく使用するし、どうやらCluade CodeもGithub copilotも、クラウドのフロンティアモデルを前提にチューニングされていそう（コンテキストを贅沢に消費し勝ち？）ので、ハーネスを調べてみると、OpenCodeやpiなどの軽量なハーネスもあるようだ、piは使いこなしが玄人っぽいので、一般向け？と思うOpenCodeを使ってみることにした。

   例：
   　スクリプトのリファクタリングをやらせてみると、コンテキストサイズが256K,128Kなどのモデルを使用していたがメモリが不足していて処理が進まなくなっているように見えたり、繰り返し同じことを思考しているように見えたり、toolでファイル更新したはずが実際には更新されなかったりなど。
   　リファクタリングをやらせてみて、これまでの中で一番手ごたえがあったので、opencode側のオプション指定やモデル（エンジン）側の工夫を試すのがよさそうと思った。

1. ollamaはそれなりに簡単だったけどllama.cppに変更
   ollamaはGGUF、mlxなど様々なモデルに対応していたのが良かったが、パラメータチューニングの面からはちょっとやりにくそうだったので、少しでもモデルに割り当てるメモリを確保したくてllama.cppで動かしてみることにした。
   OpenCodekからllama-server で呼び出せるモデルは、GGUFだけなので、単に軽く動くだけでなく、なるべく雑に投げても（コンテクストを消費しがちな処理をさせて時間をかけても）、それなりの結果が返ってくる、スクリプトとしては大きくはないが参照するTEMPLATEファイルが多数、それなりのサイズがあるものをリファクタリングようなモデルを選べると良い。というのを目標にしてみた。
   2026年9月初旬時点で、最新情報として Unsloth Dynamic 3.0で量子化した、Qwen3.8-27B-UD-Q2_K_XLが、コンテキストサイズを抑えめにすれば、動きそうだったので、これを試してみた。
   何度かパラメータをチューニングすると、これが意外なことにそれなりに安定して（ゆっくりとだが）完走してくれた。
   Ornith1.0-9B, Ornith-1.5-9B, Qwen3.8-27Bを用いてリファクタリングした。

1. 仮にも長時間20時間近く動作できたので、パラメータチューニングはこれで終わりかと思ったらそうでもなく。
   リファクタリングの次は試しにmactopというossのソース解説をやらせてみたところ、どうも上手くいかない。
   ちなみに、outputさせたのが以下のファイル

   [mactop-Ornith-1.5-9B-Q4_K_M](https://yosimax.github.io/Notes-LocalLM/case2/mactop-Ornith-1.5-9B-Q4_K_M.html)

   [mactop-Ornith-1.5-9B_Q8_0](https://yosimax.github.io/Notes-LocalLM/case2/mactop-Ornith-1.5-9B_Q8_0.html)

   [mactop-Qwen3.8-27B-UD-Q2_K_XL](https://yosimax.github.io/Notes-LocalLM/case2/mactop-Qwen3.8-27B-UD-Q2_K_XL.html)

   ここまでで、以下のような評価をしている。
   Ornith1.5−9B-Q4_K_M ：4bit量子化のせいか、少し表面的なレポート（よく言えば簡潔、必要最低限）、速度が必要で簡易な内容であれば、使い所はありそう。
   Ornith1.5−9B-Q8_0 ：8bit量子化のためか、Q4_K_Mのアウトプットと比べて、根拠を例示するなどより丁寧なレポート（っぽい）。内容も及第点で、token生成速度も4〜10 token/sec くらいは出るので、一番活用したいモデル。
   Qwen3.8−27B-UD-Q2_K_XL ：27Bとは言え、Unsloth Dynamic3.0 2bit量子化のためか、Ornith1.5−9B-Q8_0に近いが、少し劣る内容、とは言えリファクタリングをやり切っているので、2bit量子化といえども（token生成が2〜6 token/sec程度と遅かろうとも）使える実力を持っていると評価できる。

1. ここまでで、opencodeでプログラミング、リファクタリングなど週末プログラミングのお供としては、
   第一候補 Ornith1.5−9B-Q8_0
   第二候補 Qwen3.8−27B-UD-Q2_K_XL ：Ornithで思うような結果が出ない時に使ってみるとか、Planだけ使ってみるとか
   かなぁ。
   さらにデータ分析をさせようと思い、mactopのソース解説をさせた時のllama-serverのログを分析させてみた。

   [Report 1 (Ornith-1.5-9B_Q8_0_80K)](https://yosimax.github.io/Notes-LocalLM/make_reports/Notes-LocalLM-report_case2_by_Ornith-1.5-9B_Q8_0_80K.html)

   [Report 2 (Qwen3.8-27B-UD-Q2_K_XL ctx_size:80K)](https://yosimax.github.io/Notes-LocalLM/make_reports/Notes-LocalLM-report_case2_by_Qwen3.8-27B.html)

   [Report 3 (Ornith-1.5-9B_Q8_0 128K)](https://yosimax.github.io/Notes-LocalLM/make_reports/Notes-LocalLM-report_case2_by_Ornith-1.5-9B_Q8_0_128K.html)

   このデータ分析させるのに、Qwen3.8がなかなか手強かった。印象としては、Qwenの癖として既知のThinkingの繰り返しが多くて、先に進まない。というものと、Ornithよりもより詳細に分析しようとしてコンテキストを消費して、80K tokenではやりきれない感じ。compactionしては、ちょっと解析してまたすぐにcompactionしてを繰り返しているように見えた。

1. いくつかのオプションを調べて適用してみることにした。
   - opencode側の設定
      1. auto compactionがdefault有効と言うことだったが、どうも期待通りに動かない。
         →明示的に指定した。
      2. 各モデルのcontext_sizeを明示した。（OpenAi互換IFでモデルのctx_sizeを取得するはずだが）
   - llama-server (llama.cpp) 側の設定
      最終的には、以下が現在の設定、動作させている時はsleepしないように、caffeinate -imsu というコマンドを実行するというのも気がついた点でとても重要でした。長時間放置しておいて、Token生成が低下していたり、止まっていたりとこれに気がつくまで、だいぶ時間を無駄にしていた。

      ```
      llama-server \
        -m ~/llama-models/Qwen3.8-27B-UD-Q2_K_XL.gguf \
        --alias Qwen3.8-27B \
        --ctx-size 102400 \   # 結局メモリギリギリだけど 100K tokenとした。
        --cache-type-k q8_0 \ # KV Cacheの量子化は、q8_0が許容できる範囲
        --cache-type-v q8_0 \
        --flash-attn on \
        --n-gpu-layers 99 \
        --parallel 1 \        # reqは、一人で使うのでシングルでよい、2とするとctx-sizeが半分しか使えない
        --batch-size 1024 \   # 処理速度やメモリ使用効率に効くということで、
        --ubatch-size 512 \   # 一度に処理する論理サイズを1024 , 物理サイズを512 とした
        --reasoning-preserve \
        --reasoning-budget 1024 \ # Thinkingを1024 tokenで打ち止め
        --reasoning-budget-message "... I am thinking for too -- let me gather more info about the task."
        --jinja \
        --temp 0.7 --top-p 0.80 --top-k 20 --min-p 0.0 --presence-penalty 1.5 --repeat-penalty 1.0 \
        --host 127.0.0.1 --port 8080
      ```

## 現時点の結論
と言う感じで上記の設定でのメモリ使用状況はというと、llama-serverのRSSが12GBは行かないくらい。opencodeも1GB程度。
これだけみると24GB全然空いているじゃん。と見えるのですが、実際にはos全体では、Used 20〜22GBで、compactionしなければswapしない位。長時間処理させて、compactionが何度か走ると、swapが4〜5GB位となる。swapしたからといってそれほど速度低下するわけではなく安定して動作できているので、ひとまず上記のパラメータをベースに、Ornith-9B-Q8_0もctx_sizeを128K tokenくらいを指定してしばらく運用してみようと思う。

## おまけ
* エディタ兼ハーネス環境
   vscode + Gtihub copilot → zed + opencode
というか、ターミナルエミュレーターはiTerm2を使用していたけど、vscodeもiTerm2もメジャーだけど比較的fatなソフトウェアということなので、軽量なターミナル、エディタとしてzedを使ってみることにした。
   zed 全然使いこなせていないが、zedも AIコーディングのためのハーネスを持っているけど、ちょっと調べるのが億劫で、cluade codeのOSS的な、opencodeが情報ありそうと言うことでいじり始めていたので、今のところはzed + opencode + llama.cppという環境です。
* より高度なAIエージェント活用を目指すなら、まだまだ学習中だがハーネスエンジニアリング、ループエンジニアリングの実践がローカルでできるのか。が次の課題だと思うが。 少なくとも２つのモデルを動作させる環境が必要だろうと思われるので、メモリが24GBでは上記でまとめているように、単一のモデルを運用するのが精一杯。
  * 複数のモデルが必要なのは、実装とレビューや検証を行うモデルが同じだと、評価が甘くなるというかズルをしてでも正しいと見せかける修正を行ったりするらしい。
  * 構成として、opencodeなどのハーネスを別端末で実行して、llama-serverをマルチモデル実行構成にして、軽量なモデルを1〜2個、本命のモデル1個位で動作させるにしても32GB位は必要そう。
  * Localの小規模LMモデルでは、圧倒的に速度と賢さの面でクラウドのフロンティアモデルに敵わない。のはどう頑張っても覆らないのは仕方がないが、自分がやりたいことに本当にフロンティアモデルが必要なのかと言うと、人それぞれとは思うが必ずしもそうではないかなと。
  * とはいえ、お手軽と言えるのはせいぜい30万〜40万円まで（個人的にはこれも無理だけど）。ということでしばらくはモデルを単独で起動して計画、実装、検証などの度にモデルを切り替えたりするなどで、活用するかと思っている。
    * 企業で使用するなら、nvidiaのGPU(16~24GB)を複数枚構成でAIサーバーを立てたり、RTX Spark / DGX Spark (128GB)などの専用機で100〜300万円となのかな。
    * Apple siliconだとMx Pro / Maxで256GB構成とか、ワットパフォーマンスだけでなく、コストパフォーマンスも良いのかなぁ、と思ったり（個人的には到底手が届かない価格だけど） 。
* ハーネスとして、以下のような構成（要素）を持たせるらしい（何となく読み取っている内容を書き出しておく）
  * オーケストレーター
    * 各エージェントにタスクを指示、返ってきた結果を別のエージェントでレビューや検証させるなどの全体の取りまとめ役
    * 実装やレビュー、検証など具体的なタスクは行わない
  * 調査・計画
    * 実装や変更が必要な範囲を調査して、実装（改修）スコープ、方針を決定?提案?する
  * 実装
    * 指示された仕様、要望を実際に修正を行う（大規模な修正にならないように入力は単機能1件のbugfixなどスコープを小さくするのがコツだとおもわれる）
  * レビュー
    * コーディングルールやポリシー、仕様などに沿っているかをレビューする
  * 検証、QA（Quality Assurance）
    * 実際に意図したどおりに実装されているかを検証する
  * 足枷（スクリプト）
    * Hooksを用いて禁止事項が守られているかを、Agentではなくscriptで検証、ゲートを設ける

## opencodeからduckduckgoで検索するMCP serverを設定してみる

### 最新情報、最新ライブラリ情報などを検索するために？ MCP serverでInternet検索できると良さそうと言うことで設定してみる

1. [duckduckgo-mcp-server](https://github.com/nickclyde/duckduckgo-mcp-server) をインストール
   ```
   uv pip install duckduckgo-mcp-server
   ```
2. opencode.jsonの末尾（どこでもいいと思うけど）にMCP serverの設定を追加
   ```
       ...
     },
     "mcp": {
       "duckduckgo": {
         "type": "local",
         "command": ["/opt/homebrew/bin/uvx", "duckduckgo-mcp-server"]
       }
     }
   }
   ```
3. duckduckgo でHogehogeについて調べてください。などで動作確認
   Ornith1.5-9Bとの組み合わせで動作確認してみたところ、速度もそれほど気になるほどではなく、使えそう。
   懸念点は、DuckDuckGo側に負担をかけないように利用するための使い方などがわかっていないこと。
   （やたらめったら検索して、もろもろ迷惑をかけたり、制約を受けるようになると、折角無償で使わせてもらっているサービスに申し訳ない。）

   ```
   duckduckgo でepub3形式について調べてください。
   10:40 AM
   - Thought: 5.7s
   The user wants me to research epub3 format using duckduckgo. This is a read-only research task, which is appropriate in plan mode. Let me search for information about epub3 format.
   
   Let me perform the search.
   duckduckgo_search [query=EPUB 3 specification format overview, max_results=10]

   - Thought: 1.9s
   Let me fetch the W3C EPUB 3 overview page for detailed information.
   最新の W3C EPUB 3.4 スペックの概要ページを取得します。
   duckduckgo_fetch_content [url=https://w3c.github.io/epub-specs/epub34/overview/, max_length=12000]

   - Thought: 4.4s
   I have good information now. Let me also search for key technical aspects like CSS features, structure, and the OPF format to give a comprehensive overview. Let me get more content and maybe search for specific aspects.
   詳細を取得し、技術的な主要要素（構造・CSS機能・メディア対応）も確認します。
   duckduckgo_search [query=EPUB 3 CSS features MathML SVG media full color, max_results=6]
   duckduckgo_fetch_content [url=https://w3c.github.io/epub-specs/epub34/overview/, max_length=12000, start_index=12000]

   - Thought: 5.3s
   I have gathered enough comprehensive information about EPUB 3. Let me compile a concise summary of what I found. I'm in plan mode (read-only), so I should present the research findings as a report to the user.

   EPUB 3 形式についての調査結果をまとめます。
   EPUB 3 の概要
   定義
   W3C Recommendation。最新は EPUB 3.4（開発中）。3.3 が安定版。
   「EPUB 3」という形式と、.3/.4 をつける仕様番号は別物。仕様を改修しても形式は同一。3.0 で作った出版物も 3.4 で有効。
   ファイル構造（単一 ZIP コンテナ）
   中身は ZIP。指定位置に XML の 容器（OCF） があり、package document（OPF相当）の場所を指す。
   Package document（content.opf）: メタデータ・リソース一覧・spine（読み順）を定義。
   Navigation document（XHTML nav）: 目次・ランドマーク。epub:type でセクションを構造化。
   Content documents: XHTML/SVG。

   主要機能
   Web 標準基盤: HTML5（XML 構文の XHTML content document）、CSS、SVG、JavaScript。
   フルカラー対応（color-support メタデータ）。
   数学式・ベクター: MathML、SVG 内包。
   オーディオ/ビデオ: <audio>/<video> 内包。
   埋め込みフォント: OpenType / WOFF / WOFF2。
   スクリプト: 制限あり（ポータビリティ・アクセシビリティに配慮）。
   レイアウト 2種:
   Reflowable（再配置） — デバイスサイズに自動対応（デフォルト）。
   Fixed layout — 2 種類:
   Pre-paginated: 各 spine 要素が 1 ページ（童話・漫画・レシピ）。
   Roll（3.4 新機能）: 画面にフィットした連続スクロール（webtoon）。未成熟。
   メディアオーバーレイ: 音声とテキストの同期（点字・視覚障害対応）。
   多言語・国際化: ITS で翻訳、ruby 注釈、BIDI 文字、alternate-script（日本語→ローマ字等）、page-progression-direction。
   セマンティック: RDFa / Microdata / JSON-LD。
   アクセシビリティ: 別仕様（EPUB Accessibility）で評価。

   本プロジェクトへの関連
     word2epub の出力は TEMPLATE/book-template をコピペして生成している。上記の主要要素（OPF パッケージドキュメント・spine・nav・content documents・メタデータ）に対応させていると推測されます。
   調査は以上です。次への方向性として、例えば以下を調べますか？
     - word2epub 内の content.opf（package document）生成コードを確認し、上記仕様とどう対応しているか
     - 特定機能（例: 固定レイアウト・フルカラー・メディアオーバーレイ）の実装検討
     - 出力形式のバージョン（3.0 固定 vs 最新）に関する方針
   ご希望を教えてください。
   ▣  Plan · Ornith-1.5_128K · 4m 17s
   ```
