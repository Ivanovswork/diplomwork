package com.example.myapplication

import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.example.myapplication.databinding.ActivityUploadBookToChildBinding
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream

class UploadBookToChildActivity : AppCompatActivity() {

    private lateinit var binding: ActivityUploadBookToChildBinding
    private lateinit var api: DjangoApi
    private lateinit var token: String
    private var childId: Int = 0
    private var childName: String = ""
    private var selectedFileUri: Uri? = null
    private var selectedFileName: String? = null
    private var progressDialog: AlertDialog? = null

    private val pickPdfLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let {
            selectedFileUri = it
            selectedFileName = getFileName(it)
            binding.tvFileName.text = selectedFileName ?: "Файл выбран"
            binding.tvFileName.visibility = android.view.View.VISIBLE
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityUploadBookToChildBinding.inflate(layoutInflater)
        setContentView(binding.root)

        childId = intent.getIntExtra("child_id", 0)
        childName = intent.getStringExtra("child_name") ?: ""

        val prefs = getSharedPreferences("auth", MODE_PRIVATE)
        token = prefs.getString("token", "") ?: ""

        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        api = retrofit.create(DjangoApi::class.java)

        binding.tvChildName.text = childName

        binding.btnBack.setOnClickListener {
            finish()
        }

        binding.btnSelectFile.setOnClickListener {
            pickPdfLauncher.launch("application/pdf")
        }

        binding.btnUpload.setOnClickListener {
            checkLimitAndUpload()
        }
    }

    private fun checkLimitAndUpload() {
        api.getChildBookLimit("Token $token", childId).enqueue(object : Callback<CheckBookLimitResponse> {
            override fun onResponse(call: Call<CheckBookLimitResponse>, response: Response<CheckBookLimitResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    if (result.can_upload) {
                        uploadBook()
                    } else {
                        AlertDialog.Builder(this@UploadBookToChildActivity)
                            .setTitle("Лимит книг")
                            .setMessage(result.message)
                            .setPositiveButton("OK", null)
                            .show()
                    }
                }
            }

            override fun onFailure(call: Call<CheckBookLimitResponse>, t: Throwable) {
                Toast.makeText(this@UploadBookToChildActivity, "Ошибка проверки лимита", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun getFileName(uri: Uri): String? {
        val cursor = contentResolver.query(uri, null, null, null, null)
        cursor?.use {
            val nameIndex = it.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
            it.moveToFirst()
            return it.getString(nameIndex)
        }
        return null
    }

    private fun showProgress() {
        progressDialog = AlertDialog.Builder(this)
            .setTitle("Загрузка")
            .setMessage("Идет загрузка книги для ребенка... Пожалуйста, подождите")
            .setCancelable(false)
            .show()
    }

    private fun hideProgress() {
        progressDialog?.dismiss()
        progressDialog = null
    }

    private fun uploadBook() {
        val name = binding.etName.text.toString().trim()
        val dailyGoal = binding.etDailyGoal.text.toString().trim()
        val fileUri = selectedFileUri

        if (name.isEmpty()) {
            Toast.makeText(this, "Введите название книги", Toast.LENGTH_SHORT).show()
            return
        }

        if (dailyGoal.isEmpty()) {
            Toast.makeText(this, "Введите дневную цель", Toast.LENGTH_SHORT).show()
            return
        }

        if (fileUri == null) {
            Toast.makeText(this, "Выберите PDF файл", Toast.LENGTH_SHORT).show()
            return
        }

        val dailyGoalInt = dailyGoal.toIntOrNull()
        if (dailyGoalInt == null || dailyGoalInt < 1) {
            Toast.makeText(this, "Дневная цель должна быть больше 0", Toast.LENGTH_SHORT).show()
            return
        }

        showProgress()

        try {
            val parcelFileDescriptor = contentResolver.openFileDescriptor(fileUri, "r")
            val inputStream = FileInputStream(parcelFileDescriptor?.fileDescriptor)
            val tempFile = File(cacheDir, selectedFileName ?: "book.pdf")
            FileOutputStream(tempFile).use { outputStream ->
                inputStream.copyTo(outputStream)
            }

            val childIdBody = childId.toString().toRequestBody("text/plain".toMediaTypeOrNull())
            val nameBody = name.toRequestBody("text/plain".toMediaTypeOrNull())
            val dailyGoalBody = dailyGoalInt.toString().toRequestBody("text/plain".toMediaTypeOrNull())
            val fileBody = tempFile.asRequestBody("application/pdf".toMediaTypeOrNull())
            val filePart = MultipartBody.Part.createFormData("file", tempFile.name, fileBody)

            api.uploadBookToChild("Token $token", childIdBody, nameBody, dailyGoalBody, filePart)
                .enqueue(object : Callback<Map<String, Any>> {
                    override fun onResponse(call: Call<Map<String, Any>>, response: Response<Map<String, Any>>) {
                        hideProgress()
                        tempFile.delete()
                        if (response.isSuccessful) {
                            Toast.makeText(this@UploadBookToChildActivity, "Книга загружена ребенку!", Toast.LENGTH_SHORT).show()
                            finish()
                        } else {
                            val errorBody = response.errorBody()?.string()
                            Toast.makeText(this@UploadBookToChildActivity, "Ошибка: ${response.code()} - $errorBody", Toast.LENGTH_LONG).show()
                        }
                    }

                    override fun onFailure(call: Call<Map<String, Any>>, t: Throwable) {
                        hideProgress()
                        tempFile.delete()
                        Toast.makeText(this@UploadBookToChildActivity, "Ошибка: ${t.message}", Toast.LENGTH_LONG).show()
                    }
                })
        } catch (e: Exception) {
            hideProgress()
            Toast.makeText(this, "Ошибка подготовки файла: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }
}