package com.example.myapplication

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.widget.NestedScrollView
import com.example.myapplication.databinding.ActivityReadingBinding
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.io.FileOutputStream

class ReadingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityReadingBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var bookId: Int = 0
    private var bookName: String = ""
    private var sessionId: Int = 0
    private var currentPage: Int = 1
    private var totalPages: Int = 1
    private var startTime: Long = 0
    private var timerHandler = Handler(Looper.getMainLooper())
    private var timerRunnable: Runnable? = null
    private var isReading = false
    private var isBookFinished = false
    private var blockStartPage: Int = 1
    private var blockEndPage: Int = 2
    private var isWaitingForTest: Boolean = false
    private var isInReviewMode: Boolean = false
    private var pendingTestId: Int? = null
    private var contentStartPage: Int = 1
    private var pagesBeforeContent: Int = 0
    private var bookFormat: String = "pdf"

    // Для PDF
    private var currentPdfFile: File? = null
    private var isPageLoaded = false

    companion object {
        private const val TAG = "ReadingActivity"
        private const val REQUEST_CODE_TEST = 1001
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityReadingBinding.inflate(layoutInflater)
        setContentView(binding.root)

        bookId = intent.getIntExtra("book_id", 0)
        bookName = intent.getStringExtra("book_name") ?: "Книга"
        bookFormat = intent.getStringExtra("book_format") ?: "pdf"

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvBookTitle.text = bookName
        binding.btnBack.setOnClickListener { finishReading() }
        binding.btnNextPage.setOnClickListener { onNextPageClick() }

        if (bookFormat == "pdf") {
            // Для PDF используем WebView
            binding.scrollView.visibility = View.GONE
            binding.webView.visibility = View.VISIBLE
            setupWebView()
        } else {
            // Для EPUB используем TextView
            binding.webView.visibility = View.GONE
            binding.scrollView.visibility = View.VISIBLE
        }

        getOrCreateSession()
    }

    private fun setupScrollListener() {
        binding.scrollView.setOnScrollChangeListener(NestedScrollView.OnScrollChangeListener { _, _, scrollY, _, oldScrollY ->
            // Можно добавить автоматическую отметку прочитанной страницы при скролле
        })
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        binding.webView.settings.apply {
            javaScriptEnabled = true
            builtInZoomControls = true
            displayZoomControls = false
            loadWithOverviewMode = true
            useWideViewPort = true
            domStorageEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            allowUniversalAccessFromFileURLs = true
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode = WebSettings.LOAD_NO_CACHE
            setSupportZoom(true)
        }

        binding.webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                if (!isInReviewMode && !isWaitingForTest) {
                    startTimer()
                }
            }

            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                if (url == "reading://page_loaded") {
                    isPageLoaded = true
                    if (!isInReviewMode && !isWaitingForTest) {
                        startTimer()
                    }
                    return true
                }
                return false
            }
        }
    }

    private fun loadPdfPage() {
        isPageLoaded = false

        api.getPage("Token $token", bookId, currentPage).enqueue(object : Callback<ResponseBody> {
            override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
                if (response.isSuccessful && response.body() != null) {
                    try {
                        val pdfBytes = response.body()!!.bytes()
                        currentPdfFile = File(cacheDir, "page_${bookId}_${currentPage}.pdf")
                        FileOutputStream(currentPdfFile!!).use { fos ->
                            fos.write(pdfBytes)
                        }
                        val pdfUrl = "file://${currentPdfFile!!.absolutePath}"
                        val viewerHtml = createPdfViewerHtml(pdfUrl)
                        binding.webView.loadDataWithBaseURL(
                            "file://${currentPdfFile!!.parent}",
                            viewerHtml,
                            "text/html",
                            "UTF-8",
                            null
                        )
                    } catch (e: Exception) {
                        Toast.makeText(this@ReadingActivity, "Ошибка загрузки PDF", Toast.LENGTH_LONG).show()
                    }
                } else {
                    Toast.makeText(this@ReadingActivity, "Ошибка загрузки страницы", Toast.LENGTH_LONG).show()
                }
            }
            override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                Toast.makeText(this@ReadingActivity, "Сеть: ${t.message}", Toast.LENGTH_LONG).show()
            }
        })
    }

    private fun createPdfViewerHtml(pdfUrl: String): String {
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Чтение</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { width: 100%; height: 100%; background: #1a1a2e; overflow: hidden; }
        #pdf-container { 
            width: 100%; 
            height: 100%; 
            display: flex; 
            justify-content: center; 
            align-items: flex-start; 
            overflow-y: auto; 
            padding: 10px;
        }
        canvas { 
            max-width: 100%; 
            height: auto !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4); 
            border-radius: 8px; 
            margin-bottom: 10px;
        }
        .page-info { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); color: white; padding: 8px 20px; border-radius: 40px; font-size: 14px; }
    </style>
</head>
<body>
    <div id="pdf-container"></div>
    <div class="page-info">Страница $currentPage из $totalPages</div>
    <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        var pdfUrl = '$pdfUrl';
        var container = document.getElementById('pdf-container');
        pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
            pdf.getPage(1).then(function(page) {
                var viewport = page.getViewport({scale: 1});
                // Масштабируем под ширину экрана без отступов
                var scale = window.innerWidth / viewport.width;
                // Ограничиваем максимальный масштаб для читаемости
                scale = Math.min(scale, 2.0);
                var scaledViewport = page.getViewport({scale: scale});
                var canvas = document.createElement('canvas');
                canvas.width = scaledViewport.width;
                canvas.height = scaledViewport.height;
                container.appendChild(canvas);
                var context = canvas.getContext('2d');
                return page.render({canvasContext: context, viewport: scaledViewport}).promise;
            }).then(function() {
                window.location.href = 'reading://page_loaded';
            }).catch(function(error) {
                container.innerHTML = '<div style="color:white;text-align:center;margin-top:50px;">Ошибка: ' + error.message + '</div>';
            });
        });
    </script>
</body>
</html>
        """.trimIndent()
    }

    private fun onNextPageClick() {
        if (isInReviewMode) {
            if (currentPage < blockEndPage) {
                currentPage++
                loadPage()
            } else {
                createNewTestAndOpen()
            }
        } else if (isWaitingForTest) {
            Toast.makeText(this, "Сначала пройдите тест!", Toast.LENGTH_SHORT).show()
        } else {
            saveCurrentPage()
        }
    }

    private fun createNewTestAndOpen() {
        binding.btnNextPage.isEnabled = false
        binding.btnNextPage.text = "Создание теста..."

        api.retakeTest("Token $token", pendingTestId ?: 0).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                binding.btnNextPage.isEnabled = true
                binding.btnNextPage.text = "Далее"

                Log.d(TAG, "retakeTest response code: ${response.code()}")

                if (response.isSuccessful && response.body() != null) {
                    val responseBody = response.body()!!
                    Log.d(TAG, "retakeTest response body: $responseBody")

                    val newTestId = when (val id = responseBody["test_id"]) {
                        is Int -> id
                        is Double -> id.toInt()
                        is String -> id.toIntOrNull()
                        else -> null
                    }

                    Log.d(TAG, "createNewTestAndOpen: newTestId=$newTestId")

                    if (newTestId != null && newTestId > 0) {
                        pendingTestId = newTestId
                        isWaitingForTest = true
                        isInReviewMode = false

                        Handler(Looper.getMainLooper()).postDelayed({
                            startTestActivity()
                        }, 300)
                    } else {
                        Toast.makeText(this@ReadingActivity, "Ошибка: тест не создан (newTestId=$newTestId)", Toast.LENGTH_SHORT).show()
                        isInReviewMode = true
                        currentPage = blockStartPage
                        updateUI()
                        loadPage()
                    }
                } else {
                    Toast.makeText(this@ReadingActivity, "Ошибка создания теста", Toast.LENGTH_SHORT).show()
                    isInReviewMode = true
                    currentPage = blockStartPage
                    updateUI()
                    loadPage()
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                binding.btnNextPage.isEnabled = true
                binding.btnNextPage.text = "Далее"
                Log.e(TAG, "retakeTest failure: ${t.message}")
                Toast.makeText(this@ReadingActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                isInReviewMode = true
                currentPage = blockStartPage
                updateUI()
                loadPage()
            }
        })
    }

    private fun loadPage() {
        if (bookFormat == "pdf") {
            loadPdfPage()
        } else {
            // Показываем индикатор загрузки
            binding.tvBookContent.text = "Загрузка страницы $currentPage..."
            binding.tvBookContent.alpha = 0.5f

            api.getEpubText("Token $token", bookId, currentPage).enqueue(object : Callback<PageTextResponse> {
                override fun onResponse(call: Call<PageTextResponse>, response: Response<PageTextResponse>) {
                    if (response.isSuccessful && response.body() != null) {
                        val pageData = response.body()!!
                        
                        binding.tvBookContent.text = pageData.text
                        binding.tvBookContent.alpha = 1.0f
                        
                        binding.scrollView.scrollTo(0, 0)
                        
                        binding.tvPageInfo.text = "$currentPage / ${pageData.total_pages}"
                        totalPages = pageData.total_pages
                        
                        if (!isInReviewMode && !isWaitingForTest) {
                            startTimer()
                        }
                    } else {
                        Toast.makeText(this@ReadingActivity, "Ошибка загрузки страницы", Toast.LENGTH_LONG).show()
                    }
                }
                
                override fun onFailure(call: Call<PageTextResponse>, t: Throwable) {
                    Toast.makeText(this@ReadingActivity, "Ошибка сети: ${t.message}", Toast.LENGTH_LONG).show()
                    binding.tvBookContent.text = "Ошибка загрузки страницы"
                }
            })
        }
    }

    private fun formatBookText(rawText: String): String {
        // Backend уже отправляет текст с правильной структурой абзацев
        // Просто убираем лишние пустые строки в начале и конце
        return rawText.trim()
    }

    private fun getOrCreateSession() {
        api.getOrCreateSession("Token $token", bookId).enqueue(object : Callback<SessionResponse> {
            override fun onResponse(call: Call<SessionResponse>, response: Response<SessionResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val session = response.body()!!
                    sessionId = session.session_id
                    currentPage = session.current_page
                    totalPages = session.total_pages
                    blockStartPage = session.block_start_page ?: 1
                    blockEndPage = session.block_end_page ?: 2
                    isBookFinished = session.is_book_finished ?: false
                    
                    // Получаем информацию о структуре книги
                    contentStartPage = session.content_start_page ?: 1
                    pagesBeforeContent = session.pages_before_content ?: 0

                    if (isBookFinished) {
                        finish()
                        return
                    }

                    checkTestForCurrentBlock()
                    updateUI()
                    loadPage()
                } else {
                    finish()
                }
            }
            override fun onFailure(call: Call<SessionResponse>, t: Throwable) {
                finish()
            }
        })
    }

    private fun checkTestForCurrentBlock() {
        api.checkTestRequired("Token $token", sessionId).enqueue(object : Callback<CheckTestResponse> {
            override fun onResponse(call: Call<CheckTestResponse>, response: Response<CheckTestResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val check = response.body()!!
                    if (check.requires_test) {
                        isWaitingForTest = true
                        pendingTestId = check.test_id
                        showTestDialog()
                    } else {
                        isWaitingForTest = false
                        isInReviewMode = false
                        pendingTestId = null
                        updateUI()
                    }
                }
            }
            override fun onFailure(call: Call<CheckTestResponse>, t: Throwable) {}
        })
    }

    private fun showTestDialog() {
        Log.d(TAG, "showTestDialog: called with pendingTestId=$pendingTestId")

        if (pendingTestId == null || pendingTestId == 0) {
            Log.e(TAG, "showTestDialog: pendingTestId is null or 0")
            Toast.makeText(this, "Ошибка: тест не найден", Toast.LENGTH_SHORT).show()
            return
        }

        val builder = AlertDialog.Builder(this)
        builder.setTitle("Тест на понимание")
        builder.setMessage("Необходимо пройти тест, чтобы продолжить чтение.")
        builder.setPositiveButton("Пройти тест") { _, _ ->
            Log.d(TAG, "showTestDialog: user clicked Пройти тест")
            startTestActivity()
        }
        builder.setCancelable(false)

        try {
            builder.show()
            Log.d(TAG, "showTestDialog: dialog shown successfully")
        } catch (e: Exception) {
            Log.e(TAG, "showTestDialog: error showing dialog", e)
        }
    }

    private fun startTestActivity() {
        Log.d(TAG, "startTestActivity: pendingTestId=$pendingTestId, bookId=$bookId")

        if (pendingTestId == null || pendingTestId == 0) {
            Log.e(TAG, "startTestActivity: pendingTestId is null or 0")
            Toast.makeText(this, "Ошибка: тест не найден", Toast.LENGTH_SHORT).show()
            return
        }

        val intent = Intent(this, TestActivity::class.java)
        intent.putExtra("test_id", pendingTestId ?: 0)
        intent.putExtra("book_id", bookId)
        intent.putExtra("book_name", bookName)
        intent.putExtra("start_page", blockStartPage)
        intent.putExtra("end_page", blockEndPage)

        Log.d(TAG, "startTestActivity: starting TestActivity with testId=${pendingTestId}")
        startActivityForResult(intent, REQUEST_CODE_TEST)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_CODE_TEST && resultCode == RESULT_OK) {
            val testPassed = data?.getBooleanExtra("test_passed", false) ?: false
            val rereadNeeded = data?.getBooleanExtra("reread_needed", false) ?: false
            val testFailed = data?.getBooleanExtra("test_failed", false) ?: false

            if (testPassed) {
                isWaitingForTest = false
                isInReviewMode = false
                getOrCreateSession()
                Toast.makeText(this, "Тест пройден! Продолжайте чтение.", Toast.LENGTH_SHORT).show()
            } else if (rereadNeeded) {
                val startPage = data?.getIntExtra("start_page", blockStartPage) ?: blockStartPage
                isWaitingForTest = false
                isInReviewMode = true
                currentPage = startPage
                updateUI()
                loadPage()
                Toast.makeText(this, "Перечитайте страницы $startPage-$blockEndPage", Toast.LENGTH_LONG).show()
            } else if (testFailed) {
                isWaitingForTest = true
                updateUI()
                Toast.makeText(this, "Тест не пройден! Нужно пройти тест, чтобы продолжить.", Toast.LENGTH_LONG).show()
            } else {
                isWaitingForTest = true
                updateUI()
                Toast.makeText(this, "Сначала пройдите тест!", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun updateUI() {
        binding.tvPageInfo.text = "$currentPage / $totalPages"
        
        // Обновляем режим страницы
        when {
            currentPage <= pagesBeforeContent -> {
                binding.tvPageMode.text = "Содержание / Обложка"
            }
            else -> {
                binding.tvPageMode.text = "Основной текст"
            }
        }

        when {
            isInReviewMode -> {
                binding.btnNextPage.text = "Далее"
                binding.btnNextPage.isEnabled = true
            }
            isWaitingForTest -> {
                binding.btnNextPage.text = "Заблокировано"
                binding.btnNextPage.isEnabled = false
            }
            else -> {
                binding.btnNextPage.text = if (currentPage >= totalPages) "Завершить" else "Далее"
                binding.btnNextPage.isEnabled = true
            }
        }
    }

    private fun startTimer() {
        if (!isReading && !isInReviewMode && !isWaitingForTest) {
            startTime = System.currentTimeMillis()
            isReading = true
            timerRunnable = object : Runnable {
                override fun run() {
                    if (isReading) {
                        val elapsed = (System.currentTimeMillis() - startTime) / 1000
                        val minutes = elapsed / 60
                        val seconds = elapsed % 60
                        binding.tvTimer.text = String.format("%02d:%02d", minutes, seconds)
                        timerHandler.postDelayed(this, 1000)
                    }
                }
            }
            timerHandler.post(timerRunnable!!)
        }
    }

    private fun stopTimer() {
        isReading = false
        timerHandler.removeCallbacksAndMessages(null)
    }

    private fun saveCurrentPage() {
        if (!isPageLoaded && bookFormat == "pdf") {
            Toast.makeText(this, "Подождите, страница загружается", Toast.LENGTH_SHORT).show()
            return
        }

        if (currentPage >= totalPages) {
            finishReading()
            return
        }

        stopTimer()
        val timeSpent = ((System.currentTimeMillis() - startTime) / 1000).toInt()

        if (timeSpent < 5) {
            Toast.makeText(this, "Прочитайте страницу хотя бы 5 секунд", Toast.LENGTH_SHORT).show()
            startTimer()
            return
        }

        binding.btnNextPage.isEnabled = false
        binding.btnNextPage.text = "Сохранение..."

        val wordsCount = 250 + (Math.random() * 200).toInt()
        val request = SavePageRequest(sessionId, currentPage, timeSpent, wordsCount)

        api.savePageRead("Token $token", request).enqueue(object : Callback<SavePageResponse> {
            override fun onResponse(call: Call<SavePageResponse>, response: Response<SavePageResponse>) {
                binding.btnNextPage.isEnabled = true
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    currentPage++

                    if (result.is_book_finished) {
                        Toast.makeText(this@ReadingActivity, "Книга прочитана!", Toast.LENGTH_LONG).show()
                        finish()
                        return
                    }

                    if (currentPage > blockEndPage) {
                        if (result.test_created && result.test_id != null) {
                            isWaitingForTest = true
                            pendingTestId = result.test_id
                            showTestDialog()
                        } else {
                            blockStartPage = ((currentPage - 1) / 2) * 2 + 1
                            blockEndPage = blockStartPage + 1
                            updateUI()
                            loadPage()
                        }
                        return
                    }

                    updateUI()
                    loadPage()
                } else {
                    binding.btnNextPage.text = "Далее"
                    Toast.makeText(this@ReadingActivity, "Ошибка сохранения", Toast.LENGTH_SHORT).show()
                    startTimer()
                }
            }
            override fun onFailure(call: Call<SavePageResponse>, t: Throwable) {
                binding.btnNextPage.isEnabled = true
                binding.btnNextPage.text = "Далее"
                Toast.makeText(this@ReadingActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                startTimer()
            }
        })
    }

    private fun finishReading() {
        stopTimer()
        AlertDialog.Builder(this)
            .setTitle("Завершить чтение")
            .setMessage("Вы действительно хотите завершить чтение?")
            .setPositiveButton("Да") { _, _ ->
                api.finishReading("Token $token", sessionId).enqueue(object : Callback<Map<String, Boolean>> {
                    override fun onResponse(call: Call<Map<String, Boolean>>, response: Response<Map<String, Boolean>>) {
                        currentPdfFile?.delete()
                        finish()
                    }
                    override fun onFailure(call: Call<Map<String, Boolean>>, t: Throwable) {
                        currentPdfFile?.delete()
                        finish()
                    }
                })
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    override fun onBackPressed() {
        finishReading()
    }

    override fun onDestroy() {
        super.onDestroy()
        stopTimer()
        currentPdfFile?.delete()
    }
}