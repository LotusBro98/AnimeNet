package com.example.face2anime;

import android.Manifest;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.BitmapShader;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.BitmapDrawable;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Bundle;

import com.google.android.gms.vision.Frame;
import com.google.android.gms.vision.face.Face;
import com.google.android.gms.vision.face.FaceDetector;
import com.google.android.material.bottomnavigation.BottomNavigationView;


import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.content.res.ResourcesCompat;

import android.provider.MediaStore;
import android.util.SparseArray;
import android.view.MenuItem;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;

import yuku.ambilwarna.AmbilWarnaDialog;

public class MainActivity extends AppCompatActivity {
    private TextView mTextMessage;
    private Bitmap photo;
    private Bitmap head;
    private Bitmap eyes;
    private Bitmap hair;
    private Bitmap anime;

    //private String baseURL = "http://192.168.42.224"; //Gladiator local
    //private String baseURL = "http://5.188.41.199";  //Anime-Neko-World
    private String baseURL = "http://ec2-63-32-89-49.eu-west-1.compute.amazonaws.com";  //AWS

    private URL url_seg;
    private URL url_drw;

    private Painter painter;

    //static{ System.loadLibrary("opencv_java4"); }

    private BottomNavigationView.OnNavigationItemSelectedListener mOnNavigationItemSelectedListener
            = new BottomNavigationView.OnNavigationItemSelectedListener() {

        @Override
        public boolean onNavigationItemSelected(@NonNull MenuItem item) {
            ImageView imageView = findViewById(R.id.imageView);
            ImageView headView = findViewById(R.id.headView);
            ImageView eyesView = findViewById(R.id.eyesView);
            ImageView hairView = findViewById(R.id.hairView);

            switch (item.getItemId()) {
                case R.id.navigation_photo:
                    showPhoto();
                    addPhoto();
                    return true;
                case R.id.navigation_edit:
                    showEditor();
                    return true;
                case R.id.navigation_anime:
                    updateAnime();
                    showAnime();
                    //mTextMessage.setText(R.string.title_anime);
                    return true;
            }
            return false;
        }
    };

    private BottomNavigationView.OnNavigationItemSelectedListener mOnNavigationItemSelectedListenerLayer
            = new BottomNavigationView.OnNavigationItemSelectedListener() {

        @Override
        public boolean onNavigationItemSelected(@NonNull MenuItem item) {
            switch (item.getItemId()) {
                case R.id.navigation_head:
                    painter.setLayer(0);
                    return true;
                case R.id.navigation_eyes:
                    painter.setLayer(1);
                    return true;
                case R.id.navigation_hair:
                    painter.setLayer(2);
                    return true;
            }
            return false;
        }
    };

    private BottomNavigationView.OnNavigationItemSelectedListener mOnNavigationItemSelectedListenerEraseDraw
            = new BottomNavigationView.OnNavigationItemSelectedListener() {

        @Override
        public boolean onNavigationItemSelected(@NonNull MenuItem item) {
            switch (item.getItemId()) {
                case R.id.navigation_draw:
                    painter.setErase(false);
                    return true;
                case R.id.navigation_erase:
                    painter.setErase(true);
                    return true;
                case R.id.navigation_pick_color:
                    pickColor();
                    return true;
            }
            return false;
        }
    };

    private void showAnime()
    {
        ImageView imageView = findViewById(R.id.imageView);
        ImageView headView = findViewById(R.id.headView);
        ImageView eyesView = findViewById(R.id.eyesView);
        ImageView hairView = findViewById(R.id.hairView);

        imageView.setImageDrawable(new BitmapDrawable(getResources(), anime));
        imageView.setVisibility(View.VISIBLE);
        headView.setVisibility(View.INVISIBLE);
        eyesView.setVisibility(View.INVISIBLE);
        hairView.setVisibility(View.INVISIBLE);
    }

    private void showPhoto()
    {
        ImageView imageView = findViewById(R.id.imageView);
        ImageView headView = findViewById(R.id.headView);
        ImageView eyesView = findViewById(R.id.eyesView);
        ImageView hairView = findViewById(R.id.hairView);

        imageView.setImageDrawable(new BitmapDrawable(getResources(), photo));
        imageView.setVisibility(View.VISIBLE);
        headView.setVisibility(View.INVISIBLE);
        eyesView.setVisibility(View.INVISIBLE);
        hairView.setVisibility(View.INVISIBLE);
    }

    private void showEditor()
    {
        ImageView imageView = findViewById(R.id.imageView);
        ImageView headView = findViewById(R.id.headView);
        ImageView eyesView = findViewById(R.id.eyesView);
        ImageView hairView = findViewById(R.id.hairView);

        imageView.setVisibility(View.INVISIBLE);
        headView.setVisibility(View.VISIBLE);
        eyesView.setVisibility(View.VISIBLE);
        hairView.setVisibility(View.VISIBLE);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
//        requestWindowFeature(Window.FEATURE_NO_TITLE);
//        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
//                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setContentView(R.layout.activity_main);

        ImageView headView = findViewById(R.id.headView);
        ImageView eyesView = findViewById(R.id.eyesView);
        ImageView hairView = findViewById(R.id.hairView);
        painter = new Painter(headView, eyesView, hairView);

        BottomNavigationView navView = findViewById(R.id.nav_view);
        mTextMessage = findViewById(R.id.message);
        navView.setOnNavigationItemSelectedListener(mOnNavigationItemSelectedListener);

        BottomNavigationView layerNav = findViewById(R.id.layer_nav);
        layerNav.setOnNavigationItemSelectedListener(mOnNavigationItemSelectedListenerLayer);
        layerNav.setSelectedItemId(R.id.navigation_hair);

        BottomNavigationView eraseDrawNav = findViewById(R.id.nav_draw_erase);
        eraseDrawNav.setOnNavigationItemSelectedListener(mOnNavigationItemSelectedListenerEraseDraw);

        try {
            url_seg = new URL(baseURL + "/segmentize");
            url_drw = new URL(baseURL + "/draw");
        } catch (MalformedURLException e) {
            e.printStackTrace();
        }

        addPhoto();
    }

    static final int REQUEST_IMAGE_CAPTURE = 1;
    static final int REQUEST_GALLERY = 2;

    private void dispatchTakePictureIntent() {
        if (ContextCompat.checkSelfPermission(getApplicationContext(), Manifest.permission.CAMERA) == PackageManager.PERMISSION_DENIED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, REQUEST_IMAGE_CAPTURE);
            return;
        }

        Intent takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
        if (takePictureIntent.resolveActivity(getPackageManager()) != null) {
            startActivityForResult(takePictureIntent, REQUEST_IMAGE_CAPTURE);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        try {
            BottomNavigationView nav = findViewById(R.id.nav_view);
            if (painter.onTouchEvent(event) && nav.getSelectedItemId() == R.id.navigation_anime)
            {
                updateAnime();
            }
            return true;
        } catch (Exception e) {
            TextView textView = findViewById(R.id.message);
            textView.setText(e.toString());
            return true;
        }
    }

    private void dispatchGalleryIntent() {
        Intent i = new Intent(Intent.ACTION_PICK, android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
        startActivityForResult(i, REQUEST_GALLERY);
//
//        Intent intent = new Intent();
//        intent.setType("image/*");
//        intent.setAction(Intent.ACTION_GET_CONTENT);
//        if (intent.resolveActivity(getPackageManager()) != null) {
//            startActivityForResult(Intent.createChooser(intent,
//                    "Select Picture"), REQUEST_GALLERY);
//        }
    }

    private Bitmap extractFace(Bitmap image)
    {
        FaceDetector faceDetector = new
                FaceDetector.Builder(getApplicationContext()).setTrackingEnabled(false)
                .build();

//        Paint myRectPaint = new Paint();
//        myRectPaint.setStrokeWidth(5);
//        myRectPaint.setColor(Color.RED);
//        myRectPaint.setStyle(Paint.Style.STROKE);
//
//        Bitmap tempBitmap = Bitmap.createBitmap(image.getWidth(), image.getHeight(), Bitmap.Config.RGB_565);
//        Canvas tempCanvas = new Canvas(tempBitmap);
//        tempCanvas.drawBitmap(image, 0, 0, null);

        int W = image.getWidth();
        int H = image.getHeight();

        Frame frame = new Frame.Builder().setBitmap(image).build();

        SparseArray<Face> faces = faceDetector.detect(frame);

        Face face = faces.valueAt(0);

        float scale = 1.3f;

        int x = (int) face.getPosition().x;
        int y = (int) face.getPosition().y;
        int w = (int) face.getWidth();
        int h = (int) face.getHeight();

        x -= (scale - 1)/2 * w;
        y -= (scale - 1)/2 * h;
        w *= scale;
        h *= scale;

        if (x < 0)
            x = 0;
        if (x + w >= W)
            w = W - x - 1;
        if (y < 0)
            y = 0;
        if (y + h >= H)
            h = H - y - 1;

        Bitmap cropped = Bitmap.createBitmap(image, x, y, w, h);

        cropped.setHasAlpha(true);
        Bitmap scaled = Bitmap.createScaledBitmap(cropped, 256, 256, false);

        return scaled;
    }

    class RequestSegmentsTask extends AsyncTask<Bitmap, Void, Bitmap[]> {

        @Override
        protected void onPreExecute() {
            super.onPreExecute();
        }

        @Override
        protected Bitmap[] doInBackground(Bitmap... bitmaps) {
            Bitmap photo = bitmaps[0];
            return requestSegments(photo);
        }

        @Override
        protected void onPostExecute(Bitmap[] bitmap) {
            if (bitmap == null || bitmap[0] == null || bitmap[1] == null || bitmap[2] == null)
                return;

            painter.setHead(bitmap[0].copy(Bitmap.Config.ARGB_8888, true));
            painter.setEyes(bitmap[1].copy(Bitmap.Config.ARGB_8888, true));
            painter.setHair(bitmap[2].copy(Bitmap.Config.ARGB_8888, true));

            ImageView headView = findViewById(R.id.headView);
            ImageView eyesView = findViewById(R.id.eyesView);
            ImageView hairView = findViewById(R.id.hairView);

            headView.setImageDrawable(new BitmapDrawable(getResources(), painter.getHead()));
            eyesView.setImageDrawable(new BitmapDrawable(getResources(), painter.getEyes()));
            hairView.setImageDrawable(new BitmapDrawable(getResources(), painter.getHair()));

            BottomNavigationView nav = findViewById(R.id.nav_view);
            nav.setSelectedItemId(R.id.navigation_edit);
        }
    }

    class RequestAnimeTask extends AsyncTask<Bitmap, Void, Bitmap> {

        @Override
        protected void onPreExecute() {
            super.onPreExecute();
        }

        @Override
        protected Bitmap doInBackground(Bitmap... bitmaps) {
            Bitmap head = bitmaps[0];
            Bitmap eyes = bitmaps[1];
            Bitmap hair = bitmaps[2];
            return requestAnime(head, eyes, hair);
        }

        @Override
        protected void onPostExecute(Bitmap bitmap) {
//            TextView textView = findViewById(R.id.message);
//            textView.setText(bitmap);
            anime = bitmap;

            ImageView imageView = findViewById(R.id.imageView);

            imageView.setImageDrawable(new BitmapDrawable(getResources(), anime));
            //BottomNavigationView nav = findViewById(R.id.nav_view);
            //nav.setSelectedItemId(R.id.navigation_edit);
        }
    }

    private byte[] encodePng(Bitmap bitmap)
    {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.PNG, 100, baos);
        byte[] b = baos.toByteArray();
        return b;
    }

    private Bitmap[] requestSegments(Bitmap photo)
    {
        TextView textView = findViewById(R.id.message);

        try {
            byte[] photo_png_bytes = encodePng(photo);

            HttpURLConnection conn = (HttpURLConnection) url_seg.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("size", String.valueOf(photo_png_bytes.length));
            conn.setDoOutput(true);

            OutputStream wr = conn.getOutputStream();
            //OutputStreamWriter wr = new OutputStreamWriter(conn.getOutputStream());
            wr.write(photo_png_bytes);
            wr.flush();
            wr.close();

            int size_head = Integer.parseInt(conn.getHeaderField("size_head"));
            int size_eyes = Integer.parseInt(conn.getHeaderField("size_eyes"));
            int size_hair = Integer.parseInt(conn.getHeaderField("size_hair"));

            InputStream rd = conn.getInputStream();
            byte[] res_bytes = new byte[size_head + size_eyes + size_hair];
            rd.read(res_bytes);
            Bitmap head = BitmapFactory.decodeByteArray(res_bytes, 0, size_head);
            Bitmap eyes = BitmapFactory.decodeByteArray(res_bytes, size_head, size_eyes);
            Bitmap hair = BitmapFactory.decodeByteArray(res_bytes, size_head + size_eyes, size_hair);

            return new Bitmap[] {head, eyes, hair};

        } catch (Exception e) {
            //textView.setText(e.toString());
        }

        return null;
    }

    private Bitmap requestAnime(Bitmap head, Bitmap eyes, Bitmap hair)
    {
        TextView textView = findViewById(R.id.message);

        try {
            byte[] head_png_bytes = encodePng(head);
            byte[] eyes_png_bytes = encodePng(eyes);
            byte[] hair_png_bytes = encodePng(hair);

            HttpURLConnection conn = (HttpURLConnection) url_drw.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("size_head", String.valueOf(head_png_bytes.length));
            conn.setRequestProperty("size_eyes", String.valueOf(eyes_png_bytes.length));
            conn.setRequestProperty("size_hair", String.valueOf(hair_png_bytes.length));
            conn.setDoOutput(true);

            OutputStream wr = conn.getOutputStream();
            //OutputStreamWriter wr = new OutputStreamWriter(conn.getOutputStream());
            wr.write(head_png_bytes);
            wr.write(eyes_png_bytes);
            wr.write(hair_png_bytes);
            wr.flush();
            wr.close();

            //int size = Integer.parseInt(conn.getHeaderField("size"));

            InputStream rd = conn.getInputStream();

            Bitmap anime = BitmapFactory.decodeStream(rd);

            return anime;

        } catch (Exception e) {
            //textView.setText(e.toString());
        }

        return null;
    }

    private void onImageGet(Bitmap bitmap)
    {
        Bitmap cropped = extractFace(bitmap);
        cropped.setHasAlpha(true);
        this.photo = cropped.copy(Bitmap.Config.ARGB_8888, true);
        this.anime = null;
        this.head = null;
        this.eyes = null;
        this.hair = null;

        RequestSegmentsTask task = new RequestSegmentsTask();
        task.execute(cropped);

        showPhoto();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        //PhotoEditorView editorView = findViewById(R.id.photoEditorView);
        TextView textView = findViewById(R.id.message);

        try {
            if (requestCode == REQUEST_IMAGE_CAPTURE && resultCode == RESULT_OK) {
                Bundle extras = data.getExtras();
                Bitmap imageBitmap = (Bitmap) extras.get("data");
                onImageGet(imageBitmap);
            } else if (requestCode == REQUEST_GALLERY && resultCode == RESULT_OK) {
                final Uri uri = data.getData();
                Bitmap bitmap = MediaStore.Images.Media.getBitmap(this.getContentResolver(), uri);
                onImageGet(bitmap);
            }
        } catch (Exception e) {
            textView.setText(e.toString());
        }
    }

    private void addPhoto() {
        final TextView textView = findViewById(R.id.message);

        new AlertDialog.Builder(MainActivity.this)
                //.setTitle("Upload Demo")
                .setItems(R.array.image_upload_methods, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        try {
                            if (which == 0) {
                                dispatchTakePictureIntent();
                            } else {
                                dispatchGalleryIntent();
                            }
                        } catch (Exception ex) {
                            textView.setText(ex.toString());
                        }
                    }
                }).show();
    }

    @Override
    protected void onStart() {
        super.onStart();
    }

    private void updateAnime()
    {
        RequestAnimeTask task = new RequestAnimeTask();
        task.execute(painter.getHead(), painter.getEyes(), painter.getHair());
    }

    public void pickColor()
    {
        int color = painter.getLayerColor(painter.getLayer());
        final BottomNavigationView nav = findViewById(R.id.nav_draw_erase);

        AmbilWarnaDialog dialog = new AmbilWarnaDialog(this, color, false, new AmbilWarnaDialog.OnAmbilWarnaListener() {
            @Override
            public void onOk(AmbilWarnaDialog dialog, int color) {
                color = Color.argb(255, Color.red(color), Color.green(color), Color.blue(color));
                painter.setLayerColor(painter.getLayer(), color);
                updateAnime();
                nav.setSelectedItemId(R.id.navigation_draw);
            }

            @Override
            public void onCancel(AmbilWarnaDialog dialog) {
                nav.setSelectedItemId(R.id.navigation_draw);
            }
        });
        dialog.show();
    }
}
