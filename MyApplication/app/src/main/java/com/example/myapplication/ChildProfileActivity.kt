package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.myapplication.databinding.ActivityChildProfileBinding
import com.example.myapplication.databinding.ItemBookBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ChildProfileActivity : AppCompatActivity() {

    private lateinit var binding: ActivityChildProfileBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var childId: Int = 0
    private var childName: String = ""
    private var childEmail: String = ""
    private var childLimit: Int = 1
    private var childCurrentCount: Int = 0
    private var booksList = mutableListOf<Book>()
    private var isParentViewing: Boolean = false
    private var currentUserId: Int = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityChildProfileBinding.inflate(layoutInflater)
        setContentView(binding.root)

        childId = intent.getIntExtra("child_id", 0)
        childName = intent.getStringExtra("child_name") ?: ""
        childEmail = intent.getStringExtra("child_email") ?: ""
        childLimit = intent.getIntExtra("child_limit", 1)
        childCurrentCount = intent.getIntExtra("child_current_count", 0)

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        currentUserId = prefs.getInt("user_id", 0)
        isParentViewing = currentUserId != childId

        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvChildName.text = childName
        binding.tvChildEmail.text = childEmail

        binding.btnBack.setOnClickListener {
            finish()
        }

        binding.btnAddBook.setOnClickListener {
            if (isParentViewing) {
                checkLimitAndNavigate()
            } else {
                Toast.makeText(this, "Только родитель может добавлять книги", Toast.LENGTH_SHORT).show()
            }
        }

        loadBooks()
    }

    private fun checkLimitAndNavigate() {
        if (childCurrentCount >= childLimit) {
            AlertDialog.Builder(this)
                .setTitle("Лимит книг")
                .setMessage("У ребенка уже $childCurrentCount из $childLimit книг. Нельзя добавить больше.")
                .setPositiveButton("OK", null)
                .show()
            return
        }

        api.getChildBookLimit("Token $token", childId).enqueue(object : Callback<CheckBookLimitResponse> {
            override fun onResponse(call: Call<CheckBookLimitResponse>, response: Response<CheckBookLimitResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    if (result.can_upload) {
                        val intent = Intent(this@ChildProfileActivity, UploadBookToChildActivity::class.java)
                        intent.putExtra("child_id", childId)
                        intent.putExtra("child_name", childName)
                        startActivity(intent)
                    } else {
                        AlertDialog.Builder(this@ChildProfileActivity)
                            .setTitle("Лимит книг")
                            .setMessage(result.message)
                            .setPositiveButton("OK", null)
                            .show()
                    }
                }
            }

            override fun onFailure(call: Call<CheckBookLimitResponse>, t: Throwable) {
                val intent = Intent(this@ChildProfileActivity, UploadBookToChildActivity::class.java)
                intent.putExtra("child_id", childId)
                intent.putExtra("child_name", childName)
                startActivity(intent)
            }
        })
    }

    override fun onResume() {
        super.onResume()
        loadBooks()
    }

    private fun loadBooks() {
        api.getChildBooks("Token $token", childId).enqueue(object : Callback<ChildBooksResponse> {
            override fun onResponse(call: Call<ChildBooksResponse>, response: Response<ChildBooksResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    booksList = response.body()!!.child_books.toMutableList()
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

                    childCurrentCount = booksList.size
                }
            }

            override fun onFailure(call: Call<ChildBooksResponse>, t: Throwable) {
                Toast.makeText(this@ChildProfileActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun setupRecyclerView() {
        binding.rvBooks.layoutManager = LinearLayoutManager(this)
        binding.rvBooks.adapter = BooksAdapter(booksList)
    }

    private fun canDeleteBook(book: Book): Boolean {
        // Родитель может удалить любую книгу ребенка
        if (isParentViewing) {
            return true
        }

        // Ребенок может удалить только книгу, которую загрузил САМ
        // Проверяем: если книга загружена родителем (uploaded_by_id != null и uploaded_by_id != childId)
        if (book.uploaded_by_id != null && book.uploaded_by_id != childId) {
            return false
        }

        // Если uploaded_by_id == null (старые книги) или uploaded_by_id == childId (загрузил ребенок)
        return true
    }

    private fun deleteBook(book: Book) {
        if (!canDeleteBook(book)) {
            AlertDialog.Builder(this)
                .setTitle("Удаление запрещено")
                .setMessage("Эта книга была добавлена родителем. Только родитель может ее удалить.")
                .setPositiveButton("OK", null)
                .show()
            return
        }

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
                    Toast.makeText(this@ChildProfileActivity, "Книга удалена", Toast.LENGTH_SHORT).show()
                    loadBooks()
                } else {
                    val errorBody = response.errorBody()?.string()
                    Toast.makeText(this@ChildProfileActivity, "Ошибка удаления: ${response.code()} - $errorBody", Toast.LENGTH_LONG).show()
                }
            }

            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {
                Toast.makeText(this@ChildProfileActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
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
                    Toast.makeText(this@ChildProfileActivity, "Дневная цель обновлена", Toast.LENGTH_SHORT).show()
                    loadBooks()
                } else {
                    Toast.makeText(this@ChildProfileActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                Toast.makeText(this@ChildProfileActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
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

            // Показываем, кто добавил книгу
            if (book.uploaded_by_name != null) {
                holder.binding.tvUploadedBy.text = "Добавлена: ${book.uploaded_by_name}"
                holder.binding.tvUploadedBy.visibility = android.view.View.VISIBLE
            } else {
                holder.binding.tvUploadedBy.visibility = android.view.View.GONE
            }

            // Визуальное оформление кнопки удаления
            val canDelete = canDeleteBook(book)
            if (canDelete) {
                holder.binding.btnDelete.text = "Удалить"
                holder.binding.btnDelete.alpha = 1.0f
            } else {
                holder.binding.btnDelete.text = "❌"
                holder.binding.btnDelete.alpha = 0.6f
            }

            holder.binding.btnEditGoal.setOnClickListener {
                editDailyGoal(book)
            }

            holder.binding.btnDelete.setOnClickListener {
                deleteBook(book)
            }
        }

        override fun getItemCount() = books.size

        inner class ViewHolder(val binding: ItemBookBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }
}