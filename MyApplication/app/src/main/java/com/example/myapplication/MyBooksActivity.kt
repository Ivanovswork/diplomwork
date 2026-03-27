package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.myapplication.databinding.ActivityMyBooksBinding
import com.example.myapplication.databinding.ItemBookBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class MyBooksActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMyBooksBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var booksList = mutableListOf<Book>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMyBooksBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.btnBack.setOnClickListener {
            finish()
        }

        binding.btnAddBook.setOnClickListener {
            checkLimitAndNavigate()
        }

        loadBooks()
    }

    private fun checkLimitAndNavigate() {
        api.getBookLimit("Token $token").enqueue(object : Callback<CheckBookLimitResponse> {
            override fun onResponse(call: Call<CheckBookLimitResponse>, response: Response<CheckBookLimitResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    if (result.can_upload) {
                        startActivity(Intent(this@MyBooksActivity, UploadBookActivity::class.java))
                    } else {
                        AlertDialog.Builder(this@MyBooksActivity)
                            .setTitle("Лимит книг")
                            .setMessage(result.message)
                            .setPositiveButton("OK", null)
                            .show()
                    }
                } else {
                    Toast.makeText(this@MyBooksActivity, "Ошибка проверки лимита", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<CheckBookLimitResponse>, t: Throwable) {
                Toast.makeText(this@MyBooksActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    override fun onResume() {
        super.onResume()
        loadBooks()
    }

    private fun loadBooks() {
        api.getMyBooks("Token $token").enqueue(object : Callback<BooksResponse> {
            override fun onResponse(call: Call<BooksResponse>, response: Response<BooksResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    booksList = response.body()!!.my_books.toMutableList()
                    setupRecyclerView()

                    if (booksList.isEmpty()) {
                        binding.tvEmpty.visibility = android.view.View.VISIBLE
                        binding.rvBooks.visibility = android.view.View.GONE
                    } else {
                        binding.tvEmpty.visibility = android.view.View.GONE
                        binding.rvBooks.visibility = android.view.View.VISIBLE
                    }

                    binding.tvBooksCount.text = booksList.size.toString()
                    val totalPages = booksList.sumOf { it.pages_count }
                    binding.tvPagesCount.text = totalPages.toString()
                } else {
                    Toast.makeText(this@MyBooksActivity, "Ошибка загрузки книг", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<BooksResponse>, t: Throwable) {
                Toast.makeText(this@MyBooksActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun setupRecyclerView() {
        binding.rvBooks.layoutManager = LinearLayoutManager(this)
        binding.rvBooks.adapter = BooksAdapter(booksList)
    }

    private fun deleteBook(book: Book) {
        AlertDialog.Builder(this)
            .setTitle("Удаление книги")
            .setMessage("Вы уверены, что хотите удалить книгу \"${book.name}\"?\n\nЭто действие нельзя отменить.")
            .setPositiveButton("Удалить") { _, _ ->
                performDelete(book)
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun performDelete(book: Book) {
        api.deleteBook("Token $token", book.id).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(call: Call<Map<String, String>>, response: Response<Map<String, String>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@MyBooksActivity, "Книга удалена", Toast.LENGTH_SHORT).show()
                    loadBooks()
                } else {
                    val errorBody = response.errorBody()?.string()
                    Toast.makeText(this@MyBooksActivity, "Ошибка удаления: ${response.code()} - $errorBody", Toast.LENGTH_LONG).show()
                }
            }

            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {
                Toast.makeText(this@MyBooksActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun editDailyGoal(book: Book) {
        val input = android.widget.EditText(this).apply {
            hint = "Новая цель (страниц)"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER
            setText(book.daily_goal.toString())
        }

        AlertDialog.Builder(this)
            .setTitle("Изменить дневную цель")
            .setMessage("Текущая цель: ${book.daily_goal} страниц")
            .setView(input)
            .setPositiveButton("Сохранить") { _, _ ->
                val newGoalStr = input.text.toString().trim()
                if (newGoalStr.isEmpty()) {
                    Toast.makeText(this, "Введите дневную цель", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }
                val newGoal = newGoalStr.toIntOrNull()
                if (newGoal == null || newGoal < 1) {
                    Toast.makeText(this, "Дневная цель должна быть больше 0", Toast.LENGTH_SHORT).show()
                    return@setPositiveButton
                }
                updateDailyGoal(book.id, newGoal)
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun updateDailyGoal(bookId: Int, dailyGoal: Int) {
        val request = UpdateDailyGoalRequest(dailyGoal)
        api.updateDailyGoal("Token $token", bookId, request).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@MyBooksActivity, "Дневная цель обновлена", Toast.LENGTH_SHORT).show()
                    loadBooks()
                } else {
                    Toast.makeText(this@MyBooksActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                Toast.makeText(this@MyBooksActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    inner class BooksAdapter(
        private val books: List<Book>
    ) : androidx.recyclerview.widget.RecyclerView.Adapter<BooksAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = ItemBookBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val book = books[position]

            holder.binding.tvName.text = book.name
            holder.binding.tvPages.text = "${book.pages_count} стр."
            holder.binding.tvGoal.text = "Цель: ${book.daily_goal} стр./день"

            if (book.uploaded_by_name != null) {
                holder.binding.tvUploadedBy.text = "Добавлена: ${book.uploaded_by_name}"
                holder.binding.tvUploadedBy.visibility = android.view.View.VISIBLE
            } else {
                holder.binding.tvUploadedBy.visibility = android.view.View.GONE
            }

            holder.binding.btnEditGoal.setOnClickListener {
                editDailyGoal(book)
            }

            holder.binding.btnDelete.setOnClickListener {
                deleteBook(book)
            }

            holder.binding.root.setOnClickListener {
                val intent = Intent(this@MyBooksActivity, BookDetailActivity::class.java)
                intent.putExtra("book_id", book.id)
                intent.putExtra("book_name", book.name)
                startActivity(intent)
            }
        }

        override fun getItemCount() = books.size

        inner class ViewHolder(val binding: ItemBookBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }
}