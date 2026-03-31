package com.example.myapplication

import android.os.Bundle
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityTestBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class TestActivity : AppCompatActivity() {

    private lateinit var binding: ActivityTestBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var testId: Int = 0
    private var bookId: Int = 0
    private var bookName: String = ""
    private var startPage: Int = 1
    private var endPage: Int = 10
    private var questions = mutableListOf<TestQuestion>()
    private var selectedAnswers = mutableMapOf<Int, Int>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityTestBinding.inflate(layoutInflater)
        setContentView(binding.root)

        testId = intent.getIntExtra("test_id", 0)
        bookId = intent.getIntExtra("book_id", 0)
        bookName = intent.getStringExtra("book_name") ?: "Книга"
        startPage = intent.getIntExtra("start_page", 1)
        endPage = intent.getIntExtra("end_page", 10)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvBookTitle.text = bookName
        binding.tvPagesRange.text = "Страницы $startPage - $endPage"
        binding.btnBack.setOnClickListener { finish() }
        binding.btnSubmit.setOnClickListener { submitTest() }

        loadTest()
    }

    private fun loadTest() {
        api.getTest("Token $token", testId).enqueue(object : Callback<TestResponse> {
            override fun onResponse(call: Call<TestResponse>, response: Response<TestResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val test = response.body()!!
                    questions = test.questions.toMutableList()
                    setupQuestions()
                } else {
                    Toast.makeText(this@TestActivity, "Ошибка загрузки теста", Toast.LENGTH_SHORT).show()
                    finish()
                }
            }

            override fun onFailure(call: Call<TestResponse>, t: Throwable) {
                Toast.makeText(this@TestActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
                finish()
            }
        })
    }

    private fun setupQuestions() {
        binding.questionsContainer.removeAllViews()

        for ((index, question) in questions.withIndex()) {
            val questionLayout = createQuestionView(index, question)
            binding.questionsContainer.addView(questionLayout)
        }
    }

    private fun createQuestionView(index: Int, question: TestQuestion): android.view.View {
        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(0, 0, 0, 32)
        }

        val questionText = android.widget.TextView(this).apply {
            text = "${index + 1}. ${question.text}"
            textSize = 16f
            setTextColor(resources.getColor(android.R.color.white, null))
            setPadding(0, 0, 0, 16)
        }
        layout.addView(questionText)

        val radioGroup = RadioGroup(this).apply {
            id = android.view.View.generateViewId()
            orientation = RadioGroup.VERTICAL
        }

        for (answer in question.answers) {
            val radioButton = RadioButton(this).apply {
                text = answer.text
                id = android.view.View.generateViewId()
                setTextColor(resources.getColor(android.R.color.white, null))
                setPadding(0, 8, 0, 8)
                tag = answer.id
            }
            radioGroup.addView(radioButton)
        }

        radioGroup.setOnCheckedChangeListener { _, checkedId ->
            val radioButton = findViewById<RadioButton>(checkedId)
            val answerId = radioButton?.tag as? Int
            if (answerId != null) {
                selectedAnswers[question.id] = answerId
            }
        }

        layout.addView(radioGroup)
        return layout
    }

    private fun submitTest() {
        // Проверяем, что на все вопросы даны ответы
        if (selectedAnswers.size < questions.size) {
            Toast.makeText(this, "Ответьте на все вопросы", Toast.LENGTH_SHORT).show()
            return
        }

        binding.btnSubmit.isEnabled = false
        binding.btnSubmit.text = "Отправка..."

        val request = SubmitTestRequest(selectedAnswers.mapKeys { it.key.toString() })

        api.submitTest("Token $token", testId, request).enqueue(object : Callback<SubmitTestResponse> {
            override fun onResponse(call: Call<SubmitTestResponse>, response: Response<SubmitTestResponse>) {
                binding.btnSubmit.isEnabled = true
                binding.btnSubmit.text = "Отправить"

                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!

                    if (result.passed) {
                        Toast.makeText(this@TestActivity, "✅ Тест пройден!", Toast.LENGTH_LONG).show()
                        val intent = intent
                        intent.putExtra("test_passed", true)
                        setResult(RESULT_OK, intent)
                        finish()
                    } else {
                        Toast.makeText(this@TestActivity, result.message, Toast.LENGTH_LONG).show()
                        // Показываем кнопку для пересдачи
                        binding.btnRetake.visibility = android.view.View.VISIBLE
                        binding.btnRetake.setOnClickListener {
                            retakeTest()
                        }
                    }
                } else {
                    Toast.makeText(this@TestActivity, "Ошибка отправки", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<SubmitTestResponse>, t: Throwable) {
                binding.btnSubmit.isEnabled = true
                binding.btnSubmit.text = "Отправить"
                Toast.makeText(this@TestActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun retakeTest() {
        api.retakeTest("Token $token", testId).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful && response.body() != null) {
                    val newTestId = response.body()!!["test_id"] as? Int
                    if (newTestId != null) {
                        testId = newTestId
                        selectedAnswers.clear()
                        loadTest()
                        binding.btnRetake.visibility = android.view.View.GONE
                        Toast.makeText(this@TestActivity, "Новый тест создан", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Toast.makeText(this@TestActivity, "Ошибка создания нового теста", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                Toast.makeText(this@TestActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }
}