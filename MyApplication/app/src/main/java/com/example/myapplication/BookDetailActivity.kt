package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityBookDetailBinding
import okhttp3.OkHttpClient
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class BookDetailActivity : AppCompatActivity() {

    private lateinit var binding: ActivityBookDetailBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var bookId: Int = 0
    private var bookName: String = ""
    private var readOnly: Boolean = false

    companion object {
        private const val TAG = "BookDetailActivity"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityBookDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        bookId = intent.getIntExtra("book_id", 0)
        bookName = intent.getStringExtra("book_name") ?: "Книга"
        readOnly = intent.getBooleanExtra("read_only", false)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        // Добавляем логирование через OkHttp Interceptor
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request()
                Log.d(TAG, "Request: ${request.method} ${request.url}")
                val response = chain.proceed(request)
                val body = response.peekBody(Long.MAX_VALUE)
                Log.d(TAG, "Response: ${response.code}")
                Log.d(TAG, "Body: ${body.string()}")
                response
            }
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvBookTitle.text = bookName
        binding.btnBack.setOnClickListener { finish() }

        if (readOnly) {
            binding.btnRead.visibility = android.view.View.GONE
        } else {
            binding.btnRead.visibility = android.view.View.VISIBLE
            binding.btnRead.setOnClickListener { startReading() }
        }

        loadBookStats()
    }

    override fun onResume() {
        super.onResume()
        if (bookId != 0) {
            loadBookStats()
        }
    }

    private fun loadBookStats() {
        api.getBookStatsWithDaily("Token $token", bookId).enqueue(object : Callback<BookStatsResponse> {
            override fun onResponse(call: Call<BookStatsResponse>, response: Response<BookStatsResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val stats = response.body()!!
                    Log.d(TAG, "=== ПАРСИНГ УСПЕШЕН ===")
                    Log.d(TAG, "daily_goal: ${stats.daily_goal}")
                    Log.d(TAG, "pages_read_today: ${stats.pages_read_today}")
                    Log.d(TAG, "daily_goal_achieved: ${stats.daily_goal_achieved}")
                    Log.d(TAG, "daily_goal_percent: ${stats.daily_goal_percent}")
                    Log.d(TAG, "daily_goal_remaining: ${stats.daily_goal_remaining}")
                    updateUI(stats)
                } else {
                    Log.e(TAG, "Response не успешен: ${response.code()}")
                    Toast.makeText(this@BookDetailActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<BookStatsResponse>, t: Throwable) {
                Log.e(TAG, "Failure: ${t.message}")
                Toast.makeText(this@BookDetailActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun updateUI(stats: BookStatsResponse) {
        // Прогресс чтения
        binding.tvPagesRead.text = "${stats.pages_read} / ${stats.total_pages}"
        binding.progressBar.progress = stats.progress_percent.toInt()
        binding.tvProgressPercent.text = "${stats.progress_percent.toInt()}%"

        // Время
        binding.tvTotalTime.text = stats.total_time_formatted
        binding.tvAvgTimePerPage.text = formatTime(stats.avg_time_per_page_seconds)

        // Слова и скорость
        binding.tvTotalWords.text = stats.total_words.toString()
        binding.tvReadingSpeed.text = "${stats.reading_speed_wpm.toInt()} слов/мин"

        // Сессии
        binding.tvTotalSessions.text = stats.total_sessions.toString()

        // ========== ДНЕВНАЯ ЦЕЛЬ ==========
        binding.tvDailyGoal.text = "${stats.pages_read_today} / ${stats.daily_goal} стр."

        val remaining = stats.daily_goal_remaining
        binding.tvDailyGoalRemaining.text = if (remaining > 0) "Осталось: $remaining стр." else "Цель достигнута!"

        binding.dailyGoalProgress.progress = stats.daily_goal_percent

        if (stats.daily_goal_achieved) {
            binding.tvDailyGoalStatus.text = "✅ Дневная цель выполнена! 🎉"
            binding.tvDailyGoalStatus.setTextColor(resources.getColor(android.R.color.holo_green_dark, null))
        } else {
            binding.tvDailyGoalStatus.text = "📖 Осталось $remaining стр."
            binding.tvDailyGoalStatus.setTextColor(resources.getColor(android.R.color.holo_orange_dark, null))
        }

        // Кнопка чтения
        if (stats.has_active_session) {
            binding.btnRead.text = "Продолжить чтение"
        } else {
            binding.btnRead.text = "Начать чтение"
        }
    }

    private fun formatTime(seconds: Double): String {
        val secs = seconds.toInt()
        val minutes = secs / 60
        val remainingSecs = secs % 60
        return if (minutes > 0) {
            "${minutes}м ${remainingSecs}с"
        } else {
            "${secs}с"
        }
    }

    private fun startReading() {
        val intent = Intent(this, ReadingActivity::class.java)
        intent.putExtra("book_id", bookId)
        intent.putExtra("book_name", bookName)
        startActivity(intent)
    }
}