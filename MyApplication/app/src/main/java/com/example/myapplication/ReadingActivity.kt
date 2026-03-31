package com.example.myapplication

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
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
    private var isPageLoaded = false
    private var currentPdfFile: File? = null
    private var dailyGoalAchievedNotified = false

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
        Log.d(TAG, "onCreate: bookId=$bookId, bookName=$bookName")

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvBookTitle.text = bookName
        binding.btnBack.setOnClickListener { finishReading() }
        binding.btnNextPage.setOnClickListener { saveCurrentPage() }

        setupWebView()
        getOrCreateSession()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        Log.d(TAG, "setupWebView")
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
            defaultTextEncodingName = "utf-8"
        }

        binding.webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                Log.d(TAG, "onPageFinished: $url")
            }

            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                if (url == "reading://page_loaded") {
                    isPageLoaded = true
                    startTimer()
                    Toast.makeText(this@ReadingActivity, "📖 Страница $currentPage готова", Toast.LENGTH_SHORT).show()
                    return true
                }
                return false
            }
        }
    }

    private fun loadPage() {
        Log.d(TAG, "loadPage: page=$currentPage, totalPages=$totalPages")
        isPageLoaded = false

        api.getPage("Token $token", bookId, currentPage).enqueue(object : Callback<ResponseBody> {
            override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
                Log.d(TAG, "getPage response: ${response.code()}")
                if (response.isSuccessful && response.body() != null) {
                    try {
                        val pdfBytes = response.body()!!.bytes()
                        currentPdfFile = File(cacheDir, "page_${bookId}_${currentPage}.pdf")
                        FileOutputStream(currentPdfFile!!).use { fos ->
                            fos.write(pdfBytes)
                        }
                        Log.d(TAG, "PDF saved: ${currentPdfFile!!.length()} bytes")

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
                        Log.e(TAG, "PDF error: ${e.message}", e)
                        Toast.makeText(this@ReadingActivity, "Ошибка PDF: ${e.message}", Toast.LENGTH_LONG).show()
                    }
                } else {
                    Log.e(TAG, "getPage failed: ${response.code()}")
                    Toast.makeText(this@ReadingActivity, "Сервер: ${response.code()}", Toast.LENGTH_LONG).show()
                }
            }

            override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                Log.e(TAG, "Network failure: ${t.message}", t)
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes, viewport-fit=cover">
    <title>Страница $currentPage</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        html, body { width: 100%; height: 100%; background: #1a1a2e; overflow: hidden; position: fixed; top: 0; left: 0; }
        #pdf-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; background: #1a1a2e; overflow: auto; -webkit-overflow-scrolling: touch; }
        #pdf-canvas { display: block; width: auto; height: auto; max-width: 100%; max-height: 100%; object-fit: contain; box-shadow: 0 8px 32px rgba(0,0,0,0.4); border-radius: 8px; cursor: grab; touch-action: pinch-zoom pan-x pan-y; }
        #pdf-canvas:active { cursor: grabbing; }
        .loading { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #e0e7ff; font-size: 18px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; background: rgba(0,0,0,0.8); padding: 20px 32px; border-radius: 48px; backdrop-filter: blur(10px); z-index: 100; white-space: nowrap; }
        .page-info { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); color: #e0e7ff; padding: 8px 20px; border-radius: 40px; font-size: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-weight: 500; backdrop-filter: blur(20px); z-index: 100; pointer-events: none; }
        @media (max-width: 600px) { .page-info { bottom: 12px; padding: 6px 16px; font-size: 12px; } .loading { font-size: 14px; padding: 16px 24px; } }
    </style>
</head>
<body>
    <div id="pdf-container"><div class="loading">📖 Загрузка страницы $currentPage из $totalPages...</div></div>
    <div class="page-info">Страница <strong>$currentPage</strong> из <strong>$totalPages</strong></div>
    <script>
        (function() {
            console.log('PDF.js viewer starting...');
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            var pdfUrl = '$pdfUrl';
            var container = document.getElementById('pdf-container');
            var loadingDiv = document.querySelector('.loading');
            var maxScale = 2.5, minScale = 0.8, currentScale = 1.2;
            function renderPage(page, scale) {
                var viewport = page.getViewport({scale: scale});
                var canvas = document.createElement('canvas');
                canvas.id = 'pdf-canvas';
                canvas.width = viewport.width;
                canvas.height = viewport.height;
                canvas.style.width = 'auto';
                canvas.style.height = 'auto';
                canvas.style.maxWidth = '100%';
                canvas.style.maxHeight = '100%';
                container.innerHTML = '';
                container.appendChild(canvas);
                var context = canvas.getContext('2d');
                return page.render({canvasContext: context, viewport: viewport}).promise;
            }
            function adjustScaleAndRender(page) {
                var viewport = page.getViewport({scale: 1});
                var scaleByWidth = (window.innerWidth - 40) / viewport.width;
                var scaleByHeight = (window.innerHeight - 80) / viewport.height;
                currentScale = Math.min(scaleByWidth, scaleByHeight, maxScale);
                currentScale = Math.max(currentScale, minScale);
                return renderPage(page, currentScale);
            }
            pdfjsLib.getDocument(pdfUrl).promise
                .then(function(pdf) { return pdf.getPage(1); })
                .then(function(page) {
                    loadingDiv.textContent = '🎨 Рендеринг страницы...';
                    return adjustScaleAndRender(page);
                })
                .then(function() {
                    loadingDiv.style.display = 'none';
                    window.location.href = 'reading://page_loaded';
                })
                .catch(function(error) {
                    loadingDiv.innerHTML = '❌ Ошибка: ' + error.message;
                    loadingDiv.style.backgroundColor = '#ff6b6b';
                });
            window.addEventListener('resize', function() {
                if (window.pdfPage) adjustScaleAndRender(window.pdfPage);
            });
        })();
    </script>
</body>
</html>
        """.trimIndent()
    }

    private fun getOrCreateSession() {
        api.getOrCreateSession("Token $token", bookId).enqueue(object : Callback<SessionResponse> {
            override fun onResponse(call: Call<SessionResponse>, response: Response<SessionResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val session = response.body()!!
                    sessionId = session.session_id
                    currentPage = session.current_page
                    totalPages = session.total_pages

                    updateDailyGoal()  // Загружаем дневную цель при старте

                    updateUI()
                    loadPage()
                } else {
                    Toast.makeText(this@ReadingActivity, "Ошибка сессии", Toast.LENGTH_SHORT).show()
                    finish()
                }
            }
            override fun onFailure(call: Call<SessionResponse>, t: Throwable) {
                Toast.makeText(this@ReadingActivity, "Сеть: ${t.message}", Toast.LENGTH_SHORT).show()
                finish()
            }
        })
    }

    // ========== НОВЫЙ МЕТОД ДЛЯ ОБНОВЛЕНИЯ СТАТИСТИКИ ==========
    private fun updateDailyGoal() {
        api.getBookStatsWithDaily("Token $token", bookId).enqueue(object : Callback<BookStatsResponse> {
            override fun onResponse(call: Call<BookStatsResponse>, response: Response<BookStatsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    Log.d(TAG, "Daily goal: pages_read=${stats.pages_read}, pages_today=${stats.pages_read_today}, goal=${stats.daily_goal}")

                    if (!stats.daily_goal_achieved) {
                        binding.tvDailyGoal.visibility = android.view.View.VISIBLE
                        binding.tvDailyGoal.text = "Цель: ${stats.pages_read_today}/${stats.daily_goal} стр."
                        dailyGoalAchievedNotified = false
                    } else {
                        binding.tvDailyGoal.visibility = android.view.View.GONE
                        dailyGoalAchievedNotified = true
                    }
                }
            }
            override fun onFailure(call: Call<BookStatsResponse>, t: Throwable) {}
        })
    }

    private fun updateUI() {
        binding.tvPageInfo.text = "$currentPage / $totalPages"
        binding.btnNextPage.isEnabled = true
        binding.btnNextPage.text = if (currentPage >= totalPages) "Завершить" else "Далее"
    }

    private fun startTimer() {
        if (!isReading && isPageLoaded) {
            startTime = System.currentTimeMillis()
            isReading = true
            timerRunnable = object : Runnable {
                override fun run() {
                    if (isReading) {
                        val elapsed = (System.currentTimeMillis() - startTime) / 1000
                        val minutes = (elapsed / 60).toInt()
                        val seconds = (elapsed % 60).toInt()
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
        if (!isPageLoaded) {
            Toast.makeText(this, "⏳ Загрузка страницы...", Toast.LENGTH_SHORT).show()
            return
        }

        // Проверяем, нужно ли проходить тест
        api.checkTestRequired("Token $token", sessionId).enqueue(object : Callback<CheckTestResponse> {
            override fun onResponse(call: Call<CheckTestResponse>, response: Response<CheckTestResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val check = response.body()!!
                    if (check.requires_test) {
                        showTestRequiredDialog(check)
                        return
                    }
                }
                performSavePage()
            }
            override fun onFailure(call: Call<CheckTestResponse>, t: Throwable) {
                performSavePage()
            }
        })
    }

    private fun showTestRequiredDialog(check: CheckTestResponse) {
        val message = if (check.retake) {
            "Тест не пройден. Перечитайте страницы ${check.start_page}-${check.end_page} и пройдите тест заново."
        } else {
            check.message ?: "Пройдите тест перед продолжением чтения"
        }

        AlertDialog.Builder(this)
            .setTitle("Тест на понимание")
            .setMessage(message)
            .setPositiveButton("Пройти тест") { _, _ ->
                val intent = Intent(this, TestActivity::class.java)
                intent.putExtra("test_id", check.test_id)
                intent.putExtra("book_id", bookId)
                intent.putExtra("book_name", bookName)
                intent.putExtra("start_page", check.start_page ?: 1)
                intent.putExtra("end_page", check.end_page ?: 10)
                startActivityForResult(intent, REQUEST_CODE_TEST)
            }
            .setNegativeButton("Перечитать страницы") { _, _ ->
                val startPage = check.start_page ?: 1
                currentPage = startPage
                updateUI()
                loadPage()
            }
            .setCancelable(false)
            .show()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_CODE_TEST && resultCode == RESULT_OK) {
            val testPassed = data?.getBooleanExtra("test_passed", false) ?: false
            if (testPassed) {
                performSavePage()
            } else {
                Toast.makeText(this, "Тест не пройден. Перечитайте страницы и попробуйте снова.", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun performSavePage() {
        stopTimer()
        val timeSpent = ((System.currentTimeMillis() - startTime) / 1000).toInt()

        if (timeSpent < 5) {
            Toast.makeText(this, "Прочитай хотя бы 5 сек 😊", Toast.LENGTH_SHORT).show()
            startTimer()
            return
        }

        binding.btnNextPage.isEnabled = false
        binding.btnNextPage.text = "Сохраняем..."

        val wordsCount = 250 + (Math.random() * 200).toInt()
        val request = SavePageRequest(sessionId, currentPage, timeSpent, wordsCount)

        api.savePageRead("Token $token", request).enqueue(object : Callback<SavePageResponse> {
            override fun onResponse(call: Call<SavePageResponse>, response: Response<SavePageResponse>) {
                binding.btnNextPage.isEnabled = true
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    Toast.makeText(this@ReadingActivity, "✅ $currentPage сохранена ($timeSpent сек)", Toast.LENGTH_SHORT).show()
                    currentPdfFile?.delete()

                    // ========== ВАЖНО: ОБНОВЛЯЕМ СТАТИСТИКУ ПОСЛЕ СОХРАНЕНИЯ ==========
                    updateDailyGoal()

                    // Проверяем, создан ли тест
                    if (result.test_created) {
                        Toast.makeText(this@ReadingActivity, "📝 Создан новый тест! Пройдите его перед продолжением.", Toast.LENGTH_LONG).show()
                        api.checkTestRequired("Token $token", sessionId).enqueue(object : Callback<CheckTestResponse> {
                            override fun onResponse(call: Call<CheckTestResponse>, response: Response<CheckTestResponse>) {
                                if (response.isSuccessful && response.body() != null) {
                                    val check = response.body()!!
                                    if (check.requires_test) {
                                        showTestRequiredDialog(check)
                                        return
                                    }
                                }
                            }
                            override fun onFailure(call: Call<CheckTestResponse>, t: Throwable) {}
                        })
                    }

                    currentPage++

                    if (currentPage > totalPages) {
                        Toast.makeText(this@ReadingActivity, "📖 Книга прочитана! Поздравляем!", Toast.LENGTH_LONG).show()
                        finishReading()
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
                Toast.makeText(this@ReadingActivity, "Сеть: ${t.message}", Toast.LENGTH_SHORT).show()
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
                closeSession()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun closeSession() {
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

    override fun onBackPressed() {
        finishReading()
    }

    override fun onDestroy() {
        super.onDestroy()
        stopTimer()
        currentPdfFile?.delete()
    }
}