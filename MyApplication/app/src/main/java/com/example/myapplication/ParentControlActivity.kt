package com.example.myapplication

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.myapplication.databinding.ActivityParentControlBinding
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class ParentControlActivity : AppCompatActivity() {

    private lateinit var binding: ActivityParentControlBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var childrenList = mutableListOf<Child>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityParentControlBinding.inflate(layoutInflater)
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

        binding.btnAddChild.setOnClickListener {
            val email = binding.etChildEmail.text.toString().trim()
            if (email.isEmpty()) {
                Toast.makeText(this, "Введите email ребенка", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            addChildByEmail(email)
        }

        loadChildren()
    }

    private fun loadChildren() {
        api.listChildren("Token $token").enqueue(object : Callback<ChildrenListResponse> {
            override fun onResponse(call: Call<ChildrenListResponse>, response: Response<ChildrenListResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    childrenList = response.body()!!.children.toMutableList()
                    setupRecyclerView()

                    if (childrenList.isEmpty()) {
                        binding.tvEmpty.visibility = android.view.View.VISIBLE
                        binding.rvChildren.visibility = android.view.View.GONE
                    } else {
                        binding.tvEmpty.visibility = android.view.View.GONE
                        binding.rvChildren.visibility = android.view.View.VISIBLE
                    }
                }
            }

            override fun onFailure(call: Call<ChildrenListResponse>, t: Throwable) {
                Toast.makeText(this@ParentControlActivity, "Ошибка загрузки: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun setupRecyclerView() {
        binding.rvChildren.layoutManager = LinearLayoutManager(this)
        binding.rvChildren.adapter = ChildrenAdapter(childrenList)
    }

    private fun addChildByEmail(email: String) {
        val request = AddByEmailRequest(email)
        api.requestParentByEmail("Token $token", request).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@ParentControlActivity, "Запрос отправлен", Toast.LENGTH_SHORT).show()
                    binding.etChildEmail.text?.clear()
                    loadChildren()
                } else {
                    when (response.code()) {
                        404 -> Toast.makeText(this@ParentControlActivity, "Пользователь не найден", Toast.LENGTH_SHORT).show()
                        400 -> Toast.makeText(this@ParentControlActivity, "Уже связаны или запрос отправлен", Toast.LENGTH_SHORT).show()
                        else -> Toast.makeText(this@ParentControlActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                    }
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                Toast.makeText(this@ParentControlActivity, "Сеть недоступна", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun removeChild(child: Child) {
        AlertDialog.Builder(this)
            .setTitle("Удаление ребенка")
            .setMessage("Вы уверены, что хотите удалить ребенка \"${child.name}\"?")
            .setPositiveButton("Удалить") { _, _ ->
                performRemoveChild(child)
            }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun performRemoveChild(child: Child) {
        val request = ConnectionRequest(child.id)
        api.unlinkByParent("Token $token", request).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(call: Call<Map<String, String>>, response: Response<Map<String, String>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@ParentControlActivity, "Ребенок удален", Toast.LENGTH_SHORT).show()
                    loadChildren()
                } else {
                    Toast.makeText(this@ParentControlActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {
                Toast.makeText(this@ParentControlActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    inner class ChildrenAdapter(
        private val children: List<Child>
    ) : androidx.recyclerview.widget.RecyclerView.Adapter<ChildrenAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = com.example.myapplication.databinding.ItemChildBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val child = children[position]
            holder.binding.tvName.text = child.name
            holder.binding.tvEmail.text = child.email

            holder.binding.btnViewBooks.setOnClickListener {
                api.getChildBookLimit("Token $token", child.id).enqueue(object : Callback<CheckBookLimitResponse> {
                    override fun onResponse(call: Call<CheckBookLimitResponse>, response: Response<CheckBookLimitResponse>) {
                        if (response.isSuccessful && response.body() != null) {
                            val result = response.body()!!
                            val intent = Intent(this@ParentControlActivity, ChildProfileActivity::class.java)
                            intent.putExtra("child_id", child.id)
                            intent.putExtra("child_name", child.name)
                            intent.putExtra("child_email", child.email)
                            intent.putExtra("child_limit", result.limit)
                            intent.putExtra("child_current_count", result.current_count)
                            startActivity(intent)
                        } else {
                            val intent = Intent(this@ParentControlActivity, ChildProfileActivity::class.java)
                            intent.putExtra("child_id", child.id)
                            intent.putExtra("child_name", child.name)
                            intent.putExtra("child_email", child.email)
                            startActivity(intent)
                        }
                    }

                    override fun onFailure(call: Call<CheckBookLimitResponse>, t: Throwable) {
                        val intent = Intent(this@ParentControlActivity, ChildProfileActivity::class.java)
                        intent.putExtra("child_id", child.id)
                        intent.putExtra("child_name", child.name)
                        intent.putExtra("child_email", child.email)
                        startActivity(intent)
                    }
                })
            }

            holder.binding.btnRemove.setOnClickListener {
                removeChild(child)
            }
        }

        override fun getItemCount() = children.size

        inner class ViewHolder(val binding: com.example.myapplication.databinding.ItemChildBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }
}