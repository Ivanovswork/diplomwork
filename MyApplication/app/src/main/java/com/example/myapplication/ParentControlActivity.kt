package com.example.myapplication

import android.os.Bundle
import android.widget.Toast
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
    private var parentsList = mutableListOf<Parent>()

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

        binding.btnAddParent.setOnClickListener {
            val email = binding.etParentEmail.text.toString().trim()
            if (email.isEmpty()) {
                Toast.makeText(this, "Введите email пользователя", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            addParentByEmail(email)
        }

        loadParents()
    }

    private fun loadParents() {
        api.listParents("Token $token").enqueue(object : Callback<ParentsListResponse> {
            override fun onResponse(call: Call<ParentsListResponse>, response: Response<ParentsListResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    parentsList = response.body()!!.parents.toMutableList()
                    setupParentsRecyclerView()

                    if (parentsList.isEmpty()) {
                        binding.tvEmpty.visibility = android.view.View.VISIBLE
                    } else {
                        binding.tvEmpty.visibility = android.view.View.GONE
                    }
                }
            }

            override fun onFailure(call: Call<ParentsListResponse>, t: Throwable) {
                Toast.makeText(this@ParentControlActivity, "Ошибка загрузки: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun setupParentsRecyclerView() {
        binding.rvParents.layoutManager = LinearLayoutManager(this)
        binding.rvParents.adapter = ParentsAdapter(parentsList)
    }

    private fun addParentByEmail(email: String) {
        val request = AddByEmailRequest(email)
        api.requestParentByEmail("Token $token", request).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@ParentControlActivity, "Запрос отправлен", Toast.LENGTH_SHORT).show()
                    binding.etParentEmail.text?.clear()
                    loadParents()
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

    private fun requestUnlink(parent: Parent) {
        val request = mapOf("target_parent_id" to parent.id)
        api.unlinkByChild("Token $token", request).enqueue(object : Callback<Map<String, Any>> {
            override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@ParentControlActivity, "Запрос на отвязку отправлен", Toast.LENGTH_SHORT).show()
                    loadParents()
                } else {
                    Toast.makeText(this@ParentControlActivity, "Ошибка: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                Toast.makeText(this@ParentControlActivity, "Ошибка: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    inner class ParentsAdapter(
        private val parents: List<Parent>
    ) : androidx.recyclerview.widget.RecyclerView.Adapter<ParentsAdapter.ViewHolder>() {

        override fun onCreateViewHolder(parent: android.view.ViewGroup, viewType: Int): ViewHolder {
            val binding = com.example.myapplication.databinding.ItemParentRelationBinding.inflate(layoutInflater, parent, false)
            return ViewHolder(binding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val parent = parents[position]
            holder.binding.tvName.text = parent.name
            holder.binding.tvEmail.text = parent.email
            holder.binding.btnUnlink.setOnClickListener {
                requestUnlink(parent)
            }
        }

        override fun getItemCount() = parents.size

        inner class ViewHolder(val binding: com.example.myapplication.databinding.ItemParentRelationBinding) :
            androidx.recyclerview.widget.RecyclerView.ViewHolder(binding.root)
    }
}